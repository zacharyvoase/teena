"""
An efficient implementation of file descriptor tee-ing in pure Python.

Tee-ing is simply copying a stream of data from a single input to multiple
outputs.
"""

import collections
from functools import partial
import os
import sys

from teena import DEFAULT_BUFSIZE, Error
from teena.fdutils import ensure_fd, close_fd, try_remove_handler
from teena.thread_loop import ThreadLoop


def tee(input_fd, output_fds, bufsize=DEFAULT_BUFSIZE):

    """
    Create a ThreadLoop which tees from one input to many outputs.

    Example:

        >>> in_pipe, out_pipe = Pipe(), Pipe()
        >>> with tee(in_pipe.read_fd, (out_pipe.write_fd, sys.stdout)):
        ...     os.write(in_pipe.write_fd, "FooBar\n")
        ...     assert os.read(out_pipe.read_fd, 8192) == "FooBar\n"
        FooBar

    In this case, input written to one pipe is copied to both stdout *and*
    another pipe. This is useful for capturing output and having it display on
    the console in real-time.
    """

    loop = ThreadLoop()

    input_fd = ensure_fd(input_fd)
    # Every output file descriptor gets its own buffer, to begin with.
    buffers = {}
    for output_fd in output_fds:
        buffers[ensure_fd(output_fd)] = collections.deque()

    def schedule_clean_up_writers():
        for output_fd, output_buffer in buffers.iteritems():
            if not output_buffer:
                try_remove_handler(loop, output_fd)
                close_fd(output_fd)
            else:
                loop.add_handler(output_fd, partial(writer, terminating=True),
                                 loop.WRITE | loop.ERROR)

    def clean_up_reader(input_fd, close=False):
        try_remove_handler(loop, input_fd)
        if close:
            close_fd(input_fd)

    def reader(fd, events):
        # If there's an error on the input, flush the output buffers, close and
        # clean up the reader, and stop.
        if events & loop.ERROR:
            schedule_clean_up_writers()
            clean_up_reader(fd, close=True)
            return

        # If there are no file descriptors to write to any more, stop, but
        # don't close the input.
        if not buffers:
            clean_up_reader(fd, close=False)
            return

        # The loop is necessary for errors like EAGAIN and EINTR.
        while True:
            try:
                data = os.read(fd, bufsize)
            except (Error.EAGAIN, Error.EINTR):
                continue
            except (Error.EPIPE, Error.ECONNRESET, Error.EIO):
                schedule_clean_up_writers()
                clean_up_reader(fd, close=True)
                return
            break

        # The source of the data for the input FD has been closed.
        if not data:
            schedule_clean_up_writers()
            clean_up_reader(fd, close=True)
            return

        # Put the chunk of data in the buffer of every registered output.
        # If an output FD has been closed, remove it from the list of buffers.
        bad_fds = []
        for output_fd, buffer in buffers.iteritems():
            buffer.appendleft(data)
            try:
                loop.add_handler(output_fd, writer, loop.WRITE | loop.ERROR)
            except Error.EBADF:
                bad_fds.append(output_fd)
        for bad_fd in bad_fds:
            del buffers[bad_fd]

    def writer(fd, events, terminating=False):
        if events & loop.ERROR:
            try_remove_handler(loop, fd)
            del buffers[fd]
            return

        # There's no input -- unschedule the writer, it'll be rescheduled again
        # when there's something for it to write.
        if not buffers[fd]:
            try_remove_handler(loop, fd)
            if terminating:
                close_fd(fd)
            return

        data = buffers[fd].pop()
        while True:
            try:
                os.write(fd, data)
            except (Error.EPIPE, Error.ECONNRESET, Error.EIO, Error.EBADF):
                del buffers[fd]
                try_remove_handler(loop, fd)
            except (Error.EAGAIN, Error.EINTR):
                continue
            break

    # Start with just the reader.
    loop.add_handler(input_fd, reader, loop.READ | loop.ERROR)

    return loop
