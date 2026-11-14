"""Tests for reusing one iPhone connection across read operations. Run: python -m unittest discover tests"""
import asyncio
import os
import sys
import tempfile
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
              "cryptography.hazmat.primitives.serialization"):
    sys.modules.setdefault(_name, MagicMock())
for _exc in ("CloudConfigurationAlreadyPresentError", "MobileActivationException", "ProfileError"):
    if not isinstance(getattr(sys.modules["pymobiledevice3.exceptions"], _exc, None), type):
        setattr(sys.modules["pymobiledevice3.exceptions"], _exc, type(_exc, (Exception,), {}))

from iactivator import core  # noqa: E402


class FakeLockdown:
    def __init__(self, serial, n):
        self.serial, self.n = serial, n
        self.closed = False
        self.alive = True
        self.refreshes = 0
        self.all_values = {"ActivationState": "Unactivated"}

    async def get_value(self, domain=None, key=None):
        if not self.alive:
            raise ConnectionError("device gone")
        if domain is None and key is None:
            self.refreshes += 1
            self.all_values = {"ActivationState": "Activated"}  # what the phone says now
            return self.all_values
        return None

    async def close(self):
        self.closed = True


class Pool(unittest.TestCase):
    def setUp(self):
        self.opened = []

        async def fake_create(serial=None, **kw):
            lockdown = FakeLockdown(serial, len(self.opened))
            self.opened.append(lockdown)
            return lockdown

        self._orig = core.create_using_usbmux
        core.create_using_usbmux = fake_create
        core.CONNECTIONS = core._Connections()
        self.addCleanup(setattr, core, "create_using_usbmux", self._orig)

    def run_async(self, coro):
        return asyncio.run(coro)

    def test_reads_in_a_row_share_one_connection(self):
        async def go():
            for _ in range(3):
                async with core.device("A") as lockdown:
                    last = lockdown
            return last
        last = self.run_async(go())
        self.assertEqual(len(self.opened), 1)
        self.assertEqual(last.refreshes, 2)  # each reuse refreshed the device values
        self.assertFalse(last.closed)

    def test_reuse_refreshes_stale_values(self):
        async def go():
            async with core.device("A"):
                pass
            async with core.device("A") as lockdown:
                return lockdown.all_values["ActivationState"]
        self.assertEqual(self.run_async(go()), "Activated")

    def test_unplugged_phone_gets_a_new_connection(self):
        async def go():
            async with core.device("A") as first:
                pass
            first.alive = False
            async with core.device("A") as second:
                return first, second
        first, second = self.run_async(go())
        self.assertIsNot(first, second)
        self.assertTrue(first.closed)
        self.assertEqual(len(self.opened), 2)

    def test_error_closes_the_connection_and_it_is_not_reused(self):
        async def go():
            with self.assertRaises(ValueError):
                async with core.device("A"):
                    raise ValueError("diagnostics refused")
            async with core.device("A"):
                pass
        self.run_async(go())
        self.assertTrue(self.opened[0].closed)
        self.assertEqual(len(self.opened), 2)

    def test_idle_connection_expires(self):
        core._Connections.IDLE_SECONDS, old = 0.0, core._Connections.IDLE_SECONDS
        self.addCleanup(setattr, core._Connections, "IDLE_SECONDS", old)

        async def go():
            async with core.device("A"):
                pass
            async with core.device("A"):
                pass
        self.run_async(go())
        self.assertEqual(len(self.opened), 2)
        self.assertTrue(self.opened[0].closed)

    def test_unplugged_phones_are_tidied_by_the_device_poll(self):
        async def go():
            async with core.device("A"):
                pass
            async with core.device("B"):
                pass
            await core.CONNECTIONS.tidy(["B"])
        self.run_async(go())
        self.assertTrue(self.opened[0].closed)   # A was unplugged
        self.assertFalse(self.opened[1].closed)  # B is still connected

    def test_drop_before_a_job(self):
        async def go():
            async with core.device("A"):
                pass
            await core.CONNECTIONS.drop("A")
            async with core.device("A"):
                pass
        self.run_async(go())
        self.assertTrue(self.opened[0].closed)
        self.assertEqual(len(self.opened), 2)

    def test_two_at_once_do_not_share_or_leak(self):
        async def user(started, release):
            async with core.device("A") as lockdown:
                started.set()
                await release.wait()
                return lockdown

        async def go():
            s1, s2, release = asyncio.Event(), asyncio.Event(), asyncio.Event()
            t1 = asyncio.create_task(user(s1, release))
            await s1.wait()
            t2 = asyncio.create_task(user(s2, release))
            await s2.wait()
            release.set()
            return await t1, await t2
        a, b = self.run_async(go())
        self.assertIsNot(a, b)                      # never the same connection at the same time
        self.assertEqual(len(self.opened), 2)
        self.assertEqual(sum(c.closed for c in self.opened), 1)  # one kept, the other closed: nothing leaks


if __name__ == "__main__":
    unittest.main()
