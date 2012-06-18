"""Tests for async-I/O file descriptor tee-ing."""

from contextlib import nested
import os
import subprocess
import sys

from teena import Pipe, tee


def test_can_tee_to_two_pipes():
    with nested(Pipe(), Pipe(), Pipe()) as (p1, p2, p3):
        with tee(p1.read_fd, (p2.write_fd, p3.write_fd)).background():
            # Write to input pipe, the output should show up on one output
            # pipe and stdout (though there's no easy way to check this)
            os.write(p1.write_fd, 'foobar')
            os.close(p1.write_fd)
            assert os.read(p2.read_fd, 6) == 'foobar'
            assert os.read(p3.read_fd, 6) == 'foobar'


def test_can_tee_to_stdout_and_a_simple_pipe():
    with nested(Pipe(), Pipe()) as (p1, p2):
        with tee(p1.read_fd, (sys.stdout.fileno(), p2.write_fd)).background():
            # Write to input pipe, the output should show up on one output
            # pipe and stdout (though there's no easy way to check this)
            os.write(p1.write_fd, 'foobar')
            os.close(p1.write_fd)
            assert os.read(p2.read_fd, 6) == 'foobar'


def test_tee_can_capture_subprocess_output_and_send_to_stdout():
    with nested(Pipe(), Pipe()) as (in_pipe, out_pipe):
        with tee(in_pipe.read_fd, (sys.stdout.fileno(), out_pipe.write_fd)).background():
            echo = subprocess.Popen(['echo', 'hello'], stdout=in_pipe.write_fd)
            echo.wait()
            os.close(in_pipe.write_fd)
            captured_output = os.read(out_pipe.read_fd, 8192)
            assert captured_output == 'hello\n'


def test_tee_can_handle_pipe_closures_gracefully():
    with nested(Pipe(), Pipe(), Pipe()) as (p1, p2, p3):
        with tee(p1.read_fd, (p2.write_fd, p3.write_fd)).background():
            os.write(p1.write_fd, "Hello!\n")
            p1.close_write()
        assert p2.write_closed
        assert p3.write_closed
        assert os.read(p2.read_fd, 100) == "Hello!\n"
        assert os.read(p3.read_fd, 100) == "Hello!\n"


def test_when_input_is_closed_reading_any_output_gives_empty_string():
    with nested(Pipe(), Pipe(), Pipe()) as (p1, p2, p3):
        with tee(p1.read_fd, (p2.write_fd, p3.write_fd)).background():
            p1.close_write()
            assert os.read(p2.read_fd, 4096) == ''
            assert os.read(p3.read_fd, 4096) == ''
        assert p2.write_closed
        assert p3.write_closed
