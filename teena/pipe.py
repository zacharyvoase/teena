import errno
import os
import sys

from teena import DEFAULT_BUFSIZE, cached_property


__all__ = ['Pipe']


class Pipe(object):

    """
    An anonymous pipe, with named accessors for convenience.

        >>> pipe = Pipe()
        >>> pipe.write_file.write('hello\\n')
        >>> pipe.write_file.flush()  # Always remember to flush.
        >>> pipe.read_file.readline()
        'hello\\n'

    You can also open a pipe in non-blocking mode, if you're on POSIX:

        >>> pipe = Pipe(non_blocking=True)
        >>> pipe.read_file.readline()
        Traceback (most recent call last):
        ...
        IOError: [Errno 35] Resource temporarily unavailable

    Or use it as a context manager:

        >>> with Pipe() as pipe:
        ...    pipe.write_file.write('FOO\\n')
        ...    pipe.write_file.flush()
        ...    print repr(pipe.read_file.readline())
        'FOO\\n'
    """

    __slots__ = ('read_fd', 'write_fd', '__weakref__')

    def __init__(self, non_blocking=False):
        self.read_fd, self.write_fd = os.pipe()
        if non_blocking:
            self._set_nonblocking(self.read_fd)
            self._set_nonblocking(self.write_fd)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def __del__(self):
        self.close()

    @staticmethod
    def _set_nonblocking(fd):
        """Set a file descriptor to non-blocking mode (POSIX-only)."""
        try:
            import fcntl
        except ImportError:
            raise NotImplementedError("Non-blocking pipes are not supported on this platform")
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    @staticmethod
    def _fd_closed(fd):
        try:
            os.fstat(fd)
        except (OSError, IOError), exc:
            if exc.errno == errno.EBADF:
                return True
            raise
        return False

    @staticmethod
    def _close_fd(fd):
        try:
            os.close(fd)
        except (OSError, IOError), exc:
            if exc.errno != errno.EBADF:
                raise

    @cached_property
    def read_file(self, buffering=DEFAULT_BUFSIZE):
        """Get a file-like object for the read end of the pipe."""
        return os.fdopen(self.read_fd, 'rb', buffering)

    @cached_property
    def write_file(self, buffering=DEFAULT_BUFSIZE):
        """Get a file-like object for the write end of the pipe."""
        return os.fdopen(self.write_fd, 'wb', buffering)

    @property
    def read_closed(self):
        """True if the read end of this pipe is already closed."""
        return self._fd_closed(self.read_fd)

    @property
    def write_closed(self):
        """True if the write end of this pipe is already closed."""
        return self._fd_closed(self.write_fd)

    def close_read(self):
        """Close the read end of this pipe."""
        self._close_fd(self.read_fd)

    def close_write(self):
        """Close the write end of this pipe."""
        self._close_fd(self.write_fd)

    def close(self):
        """
        Attempt to close both ends of this pipe.

        If an error occurs when closing both ends, the error from the write end
        will be raised in preference to that of the read end, and the traceback
        from the read end will be printed to stderr.
        """
        try:
            self.close_read()
        finally:
            read_exc = sys.exc_info()
            try:
                self.close_write()
            except Exception, exc:
                if read_exc[0] is not None:
                    write_unraisable(self.close, *read_exc)
                raise


def write_unraisable(obj, exc_type, exc_value, exc_traceback):
    """A port of PyErr_WriteUnraisable directly from the CPython source."""
    print >>sys.stderr, "Exception %s: %r in %r ignored" % (exc_type,
                                                            exc_value,
                                                            obj)
