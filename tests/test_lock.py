"""Tests for the SIM / carrier-lock check. Run: python -m unittest discover tests"""
import ast
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


import asyncio  # noqa: E402
from types import SimpleNamespace  # noqa: E402
from unittest import mock  # noqa: E402

from iactivator import core, i18n  # noqa: E402


class InvalidServiceError(Exception):
    pass


class ConnectionError(Exception):  # the name requests uses
    pass


class FailingConfig:
    def __init__(self, *a):
        pass

    async def __aenter__(self):
        raise InvalidServiceError("The device does not offer the requested service.")

    async def __aexit__(self, *a):
        return False


def run(state, lock_error=None):
    lockdown = SimpleNamespace(all_values={"ActivationState": state})

    async def status(_):
        if lock_error:
            raise lock_error
        return False
    with mock.patch.object(core, "_activation_lock_status", status), \
            mock.patch.object(core, "MobileConfigService", FailingConfig):
        res = asyncio.run(core.lock_checks(lockdown))
    return {r["name"]: (r["status"], r["detail"]) for r in res}


class LockMessages(unittest.TestCase):
    def setUp(self):
        i18n.set_lang("ru")

    def test_device_refusal_is_not_blamed_on_the_internet(self):
        r = run("Unactivated", RuntimeError("No such value"))
        status, detail = r["Локатор (блокировка активации)"]
        self.assertEqual(status, "warn")
        self.assertNotIn("интернет", detail)
        self.assertIn("после активации", detail)

    def test_no_connection_says_so(self):
        try:
            try:
                raise ConnectionError("Max retries exceeded")
            except ConnectionError as inner:
                raise RuntimeError("post failed") from inner
        except RuntimeError as e:
            err = e
        status, detail = run("Unactivated", err)["Локатор (блокировка активации)"]
        self.assertIn("интернет", detail)

    def test_mdm_unavailable_before_activation_is_only_a_note(self):
        status, detail = run("Unactivated")["MDM (удалённое управление)"]
        self.assertEqual(status, "info")
        self.assertIn("после активации", detail)

    def test_mdm_unavailable_on_activated_phone_is_still_a_warning(self):
        self.assertEqual(run("Activated")["MDM (удалённое управление)"][0], "warn")


if __name__ == "__main__":
    unittest.main()
