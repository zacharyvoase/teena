import gc
import errno
import os

from nose.tools import assert_raises

from teena.pipe import Pipe


def test_pipe_gets_read_and_write_file_descriptors():
    pipe = Pipe()
    assert isinstance(pipe.read_fd, int)
    assert isinstance(pipe.write_fd, int)


def test_pipe_gets_read_and_write_file_handles():
    pipe = Pipe()
    assert hasattr(pipe.read_file, 'read')
    assert hasattr(pipe.write_file, 'write')


# No pun intended. Kind of.
def test_smoke_test_pipe():
    pipe = Pipe()
    pipe.write_file.write('FooBar\n')
    pipe.write_file.flush()
    assert pipe.read_file.readline() == 'FooBar\n'


def test_non_blocking_pipes_raise_EAGAIN_when_no_data_are_ready_to_read():
    pipe = Pipe(non_blocking=True)
    with assert_raises(IOError) as cm:
        pipe.read_file.read()
    assert cm.exception.errno == errno.EAGAIN


## Closing

def ensure_fd_closed(fd):
    with assert_raises(OSError) as cm:
        os.fstat(fd)
    assert cm.exception.errno == errno.EBADF


def ensure_pipe_closed(pipe):
    ensure_fd_closed(pipe.read_fd)
    ensure_fd_closed(pipe.write_fd)


def test_pipe_as_context_manager_closes_its_file_descriptors():
    with Pipe() as pipe:
        pass
    ensure_pipe_closed(pipe)


def test_close_closes_both_fds():
    pipe = Pipe()
    pipe.close()
    ensure_pipe_closed(pipe)


def test_closed_indicates_whether_an_fd_is_closed():
    pipe = Pipe()
    os.close(pipe.read_fd)
    assert pipe.read_closed
    os.close(pipe.write_fd)
    assert pipe.write_closed


def test_multiple_closes_are_a_noop():
    pipe = Pipe()
    pipe.close()
    pipe.close()
    ensure_pipe_closed(pipe)


def object_exists(object_id):
    return any(id(obj) == object_id for obj in gc.get_objects())


def test_pipe_closes_fds_on_garbage_collection():
    pipe = Pipe()
    ident = id(pipe)
    read_fd, write_fd = pipe.read_fd, pipe.write_fd

    # Check that the pipe gets collected.
    assert object_exists(ident)
    del pipe
    gc.collect()
    assert not object_exists(ident)

    ensure_fd_closed(read_fd)
    ensure_fd_closed(write_fd)


def test_errors_on_one_pipe_do_not_prevent_the_other_one_from_being_closed():
    class ReadFailPipe(Pipe):
        def close_read(self):
            1/0

    class WriteFailPipe(Pipe):
        def close_write(self):
            1/0

    pipe = ReadFailPipe()
    with assert_raises(ZeroDivisionError):
        pipe.close()
    ensure_fd_closed(pipe.write_fd)

    pipe = WriteFailPipe()
    with assert_raises(ZeroDivisionError):
        pipe.close()
    ensure_fd_closed(pipe.read_fd)


def test_if_both_pipes_raise_errors_on_closing_the_write_pipes_error_is_returned():
    class BothFailPipe(Pipe):
        def close_read(self):
            raise Exception("FOO")

        def close_write(self):
            raise Exception("BAR")

    pipe = BothFailPipe()
    with assert_raises(Exception) as cm:
        pipe.close()
    assert cm.exception.args == ("BAR",)
