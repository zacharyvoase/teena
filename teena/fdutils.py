"""Utilities for dealing with file descriptors."""

import os

from teena import Error


def ensure_fd(fd):
    """Ensure an argument is a file descriptor."""
    if not isinstance(fd, int):
        if not hasattr(fd, 'fileno'):
            raise TypeError("Arguments must be file descriptors, or implement fileno()")
        return fd.fileno()
    return fd


def close_fd(fd):
    """Close a file descriptor, ignoring EBADF."""
    if os.isatty(fd):
        return
    try:
        os.close(fd)
    except Error.EBADF:
        pass


def try_remove_handler(loop, fd):
    """Remove a handler from a loop, ignoring EBADF or KeyError."""
    try:
        loop.remove_handler(fd)
    except (KeyError, Error.EBADF):
        pass
