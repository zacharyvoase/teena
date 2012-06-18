from contextlib import contextmanager
import threading

import tornado.ioloop


class ThreadLoop(tornado.ioloop.IOLoop):

    """
    An IOLoop that can be run in a background thread as a context manager.

    Example:

        >>> read_fd, write_fd = os.pipe()
        >>> loop = ThreadLoop()
        >>> loop.add_handler(read_fd, process_items, loop.READ)
        >>> with loop.background():
        ...     os.write(write_fd, 'some message\n')
        ...     os.close(write_fd)

    In this case, ``process_items`` should detect an empty string from
    `os.read()`, and shut down the loop.
    """

    @contextmanager
    def background(self):
        # If the loop ever reaches a point where the only handler is the
        # 'waker', terminate it (we're not a long-running web server, so we
        # get to do this).
        def callback():
            if self.running():
                if self._handlers.keys() == [self._waker.fileno()]:
                    self.stop()
                else:
                    self.add_callback(callback)
        self.add_callback(callback)

        thread = threading.Thread(target=self.start)
        thread.daemon = True
        thread.start()
        try:
            yield
        finally:
            thread.join()
            self.close()
