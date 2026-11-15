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
              "cryptography.hazmat.primitives.serialization", "keyring"):
    sys.modules.setdefault(_name, MagicMock())
for _exc in ("CloudConfigurationAlreadyPresentError", "MobileActivationException", "ProfileError"):
    if not isinstance(getattr(sys.modules["pymobiledevice3.exceptions"], _exc, None), type):
        setattr(sys.modules["pymobiledevice3.exceptions"], _exc, type(_exc, (Exception,), {}))


import shutil  # noqa: E402
from unittest import mock  # noqa: E402

from iactivator import notify, settings  # noqa: E402


class Settings(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        p = mock.patch.object(settings, "_path", lambda: self.dir / "settings.json")
        p.start(); self.addCleanup(p.stop)

    def test_defaults_and_saving(self):
        ui = settings.load()["ui"]
        self.assertEqual((ui["notify"], ui["cleanup_days"]), (True, 0))
        settings.save_ui({"notify": False, "cleanup_days": 90})
        ui = settings.load()["ui"]
        self.assertEqual((ui["notify"], ui["cleanup_days"]), (False, 90))
        settings.save_ui({"notify": "yes", "cleanup_days": 7})  # ignored: not allowed values
        ui = settings.load()["ui"]
        self.assertEqual((ui["notify"], ui["cleanup_days"]), (False, 90))
        self.assertFalse(notify.enabled())

    def test_off_means_no_notification(self):
        settings.save_ui({"notify": False})
        with mock.patch.object(notify, "_show") as show:
            notify.phone_done("iPhone 15", "Активация", True)
        show.assert_not_called()


class MacText(unittest.TestCase):
    def test_quotes_in_names_cannot_break_the_script(self):
        cmd = notify.mac_command('✅ Активация', 'iPhone "Олег" \\ test', True)
        self.assertEqual(cmd[:2], ["osascript", "-e"])
        self.assertIn('"iPhone \\"Олег\\" \\\\ test"', cmd[2])
        self.assertIn('sound name "Glass"', cmd[2])


if __name__ == "__main__":
    unittest.main()
