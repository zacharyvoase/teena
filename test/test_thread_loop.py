import os

from teena import Error
from teena.thread_loop import ThreadLoop


def test_thread_loop_runs_in_background():
    # This is a high-level test, but with threads there's not much choice.
    read_fd, write_fd = os.pipe()
    strings = []
    def process_input(fd, events):
        while True:
            try:
                data = os.read(fd, 4096)
            except (Error.EAGAIN, Error.EINTR):
                continue
            except (Error.EPIPE, Error.ECONNRESET, Error.EIO):
                loop.stop()
                return
            break
        if not data:
            loop.stop()
        strings.append(data)

    loop = ThreadLoop()
    loop.add_handler(read_fd, process_input, loop.READ)
    with loop.background():
        os.write(write_fd, "Message 1\n")
        os.write(write_fd, "Message 2\n")
        os.close(write_fd)
    assert ''.join(strings) == "Message 1\nMessage 2\n"
