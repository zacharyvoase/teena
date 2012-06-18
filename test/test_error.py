import errno
import os

from nose.tools import assert_raises

from teena import Error


def test_Error_is_a_superclass_of_all_errors_with_an_errno():
    success = False
    try:
        raise OSError(errno.EBADF, os.strerror(errno.EBADF))
    except Error, exc:
        success = True
    assert success


def test_Error_ETYPE_is_a_superclass_of_all_ETYPE_errors():
    success = False
    try:
        raise OSError(errno.EBADF, os.strerror(errno.EBADF))
    except Error.EBADF, exc:
        success = True
    assert success

    success = False
    try:
        raise IOError(errno.EBADF, os.strerror(errno.EBADF))
    except Error.EBADF, exc:
        success = True
    assert success


def test_Error_ETYPE1_is_not_a_superclass_of_an_ETYPE2_error():
    success = False
    try:
        raise OSError(errno.EBADF, os.strerror(errno.EBADF))
    except Error.EPIPE, exc:
        success = False
    except OSError:
        success = True
    assert success


def test_can_check_for_multiple_error_types():
    # Result is not in the checked types
    success = False
    try:
        raise OSError(errno.EBADF, os.strerror(errno.EBADF))
    except (Error.EPIPE, Error.EIO), exc:
        success = False
    except OSError:
        success = True
    assert success

    # Result is in the checked types
    success = False
    try:
        raise OSError(errno.EBADF, os.strerror(errno.EBADF))
    except (Error.EPIPE, Error.EBADF), exc:
        success = True
    except OSError:
        success = False
    assert success
