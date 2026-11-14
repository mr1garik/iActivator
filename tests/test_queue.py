"""Tests for handling several iPhones one after another (auto mode). Run: python -m unittest discover tests"""
import asyncio
import os
import sys
import tempfile
import threading
import time
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("HOME", tempfile.mkdtemp())
for _name in ("pymobiledevice3", "pymobiledevice3.usbmux", "pymobiledevice3.ca", "pymobiledevice3.exceptions",
              "pymobiledevice3.lockdown", "pymobiledevice3.services", "pymobiledevice3.services.diagnostics",
              "pymobiledevice3.services.mobile_activation", "pymobiledevice3.services.mobile_config",
              "cryptography", "cryptography.x509", "cryptography.hazmat", "cryptography.hazmat.primitives",
              "cryptography.hazmat.primitives.serialization", "keyring"):
    sys.modules.setdefault(_name, MagicMock())
for _exc in ("CloudConfigurationAlreadyPresentError", "MobileActivationException", "ProfileError"):
    if not isinstance(getattr(sys.modules["pymobiledevice3.exceptions"], _exc, None), type):
        setattr(sys.modules["pymobiledevice3.exceptions"], _exc, type(_exc, (Exception,), {}))
if "fpdf" not in sys.modules:  # the report module subclasses FPDF; only its name is needed here
    sys.modules["fpdf"] = types.SimpleNamespace(FPDF=type("FPDF", (), {}))

from iactivator import core, webui  # noqa: E402


def wait_for(cond, timeout=5.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if cond():
            return True
        time.sleep(0.01)
    return False


class Queue(unittest.TestCase):
    def setUp(self):
        self.state = webui.State()
        self.connected = ["A", "B", "C"]
        self.order = []
        self.gates = {s: threading.Event() for s in "ABC"}

        async def connected_serials():
            return list(self.connected)

        self._orig = core.connected_serials
        core.connected_serials = connected_serials
        self.addCleanup(setattr, core, "connected_serials", self._orig)
        self.logged = []
        self.state.log = lambda msg, serial="", level="": self.logged.append(msg)

    def job(self, serial):
        async def run():
            self.order.append(serial)
            while not self.gates[serial].is_set():
                await asyncio.sleep(0.01)
        return run

    def test_phones_run_one_after_another(self):
        self.assertEqual(self.state.run_or_queue(self.job("A"), "A"), 0)        # starts now
        self.assertTrue(wait_for(lambda: self.order == ["A"]))
        self.assertEqual(self.state.run_or_queue(self.job("B"), "B"), 1)        # waits
        self.assertEqual(self.state.run_or_queue(self.job("C"), "C"), 2)
        self.assertEqual(self.state.run_or_queue(self.job("B"), "B"), 1)        # not added twice
        self.assertEqual(self.state.run_or_queue(self.job("A"), "A"), -1)       # already running
        self.gates["A"].set()
        self.assertTrue(wait_for(lambda: self.order == ["A", "B"]))
        self.assertEqual(self.state.current, "B")
        self.gates["B"].set()
        self.gates["C"].set()
        self.assertTrue(wait_for(lambda: self.order == ["A", "B", "C"] and not self.state.busy))
        self.assertEqual(self.state.queue, [])

    def test_unplugged_phone_is_skipped(self):
        self.state.run_or_queue(self.job("A"), "A")
        self.state.run_or_queue(self.job("B"), "B")
        self.state.run_or_queue(self.job("C"), "C")
        self.connected = ["A", "C"]  # B was unplugged while waiting
        self.gates["A"].set()
        self.gates["C"].set()
        self.assertTrue(wait_for(lambda: self.order == ["A", "C"] and not self.state.busy))
        self.assertTrue(any("пропускаю" in m for m in self.logged))

    def test_a_failing_phone_does_not_stop_the_line(self):
        async def broken():
            self.order.append("A")
            raise RuntimeError("lost connection")
        self.state.run_or_queue(self.job("B"), "B")
        self.gates["B"].set()
        self.assertTrue(wait_for(lambda: not self.state.busy))
        self.order.clear()
        self.gates["B"].clear()
        self.state.run_or_queue(broken, "A")
        self.state.run_or_queue(self.job("B"), "B")
        self.gates["B"].set()
        self.assertTrue(wait_for(lambda: self.order == ["A", "B"] and not self.state.busy))

    def test_a_manual_job_is_still_refused_while_busy(self):
        self.state.run_or_queue(self.job("A"), "A")
        self.assertTrue(wait_for(lambda: self.state.busy))
        self.assertFalse(self.state.run_job(self.job("B"), "B"))
        self.gates["A"].set()
        self.assertTrue(wait_for(lambda: not self.state.busy))


class TimeLimit(unittest.TestCase):
    def test_a_hanging_operation_is_cancelled(self):
        state = webui.State()
        cancelled = threading.Event()

        async def hangs():
            try:
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                cancelled.set()
                raise

        started = time.monotonic()
        with self.assertRaises(TimeoutError):
            state.run(hangs(), timeout=0.3)
        self.assertLess(time.monotonic() - started, 3)
        self.assertTrue(cancelled.wait(2))  # the operation itself was stopped, not left running

    def test_normal_operation_returns_its_result(self):
        async def quick():
            return 42
        self.assertEqual(webui.State().run(quick(), timeout=5), 42)


if __name__ == "__main__":
    unittest.main()
