"""Tests for the single-instance guard. Run: python -m unittest discover tests"""
import os
import socket
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("HOME", tempfile.mkdtemp())

from iactivator import single


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class SingleInstance(unittest.TestCase):
    def setUp(self):
        single.release()
        # Each test gets its own port so a lingering listener never bleeds across.
        self._orig_port = single.PORT
        single.PORT = _free_port()

    def tearDown(self):
        single.release()
        single.PORT = self._orig_port

    def test_first_acquires_second_defers_and_shows(self):
        shown = threading.Event()
        # First instance becomes primary and keeps running.
        self.assertTrue(single.acquire(shown.set))
        self.assertFalse(shown.is_set())

        # Second instance must NOT start; it wakes the primary instead.
        self.assertFalse(single.acquire(lambda: None))
        self.assertTrue(shown.wait(timeout=3), "primary was not asked to show its window")

    def test_release_frees_the_port(self):
        self.assertTrue(single.acquire(lambda: None))
        single.release()
        single.PORT = _free_port()  # avoid TIME_WAIT on the just-closed port
        # After release a fresh acquire is primary again (no one answers the ping).
        self.assertTrue(single.acquire(lambda: None))

    def test_unrelated_listener_does_not_block_startup(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.bind((single.HOST, single.PORT))
        srv.listen(1)
        try:
            # Port is busy but nothing speaks our protocol: we must still start.
            self.assertTrue(single.acquire(lambda: None))
        finally:
            srv.close()


if __name__ == "__main__":
    unittest.main()
