Teena: UNIX in Python
=====================

Teena aims to be a collection of ports of UNIX and Linux syscalls to
pure Python, with an emphasis on performance and correctness. Windows
support is not a primary concern—I’m initially targeting only
POSIX-compliant operating systems. The library uses
`Tornado <http://www.tornadoweb.org/>`_ to do efficient asynchronous
I/O.

The first version of this library will contain implementations of
``tee`` and ``splice`` which operate on files, sockets, and file
descriptors. There’s also a ``Capture`` class which behaves like
``StringIO``, but it has a ``fileno()`` and so can be used where a real
file descriptor is needed.

Example
-------

I’ll demonstrate how to capture the result of an HTTP request, whilst
efficiently streaming the response to ``stderr``.

Do the necessary imports:

::

    >>> from contextlib import closing
    >>> import teena
    >>> import os
    >>> import sys
    >>> import urllib2

Create a ``teena.Capture()`` object to capture the output:

::

    >>> capture = teena.Capture()

Open a connection using ``urllib2.urlopen()``. This connection object
has an associated file descriptor, so you can pass it directly into
``tee()``:

::

    >>> with closing(urllib2.urlopen('http://whatthecommit.com/index.txt')) as conn:
    ...     teena.tee(conn, (sys.stderr, capture.input))
    This really should not take 19 minutes to build.
    >>> print repr(capture.getvalue())
    'This really should not take 19 minutes to build.\n'

Installation
------------

::

    pip install teena

License
-------

Copyright (C) 2012 Zachary Voase

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
