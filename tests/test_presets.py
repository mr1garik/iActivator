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

sys.modules.setdefault("keyring", MagicMock())
import shutil  # noqa: E402
from unittest import mock  # noqa: E402
from iactivator import settings  # noqa: E402


class Presets(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        p = mock.patch.object(settings, "_path", lambda: self.dir / "settings.json")
        p.start(); self.addCleanup(p.stop)

    def test_save_apply_delete(self):
        vals = {"language": "pl-PL", "region": "PL", "activate": True, "ssid": "Shop", "password": "secret", "serial": "X"}
        name = settings.save_preset("  Продажа Польша  ", vals)
        self.assertEqual(name, "Продажа Польша")
        saved = settings.load()["presets"]["Продажа Польша"]
        self.assertEqual(saved["language"], "pl-PL")
        self.assertIn("ssid", saved)
        self.assertNotIn("password", saved)   # no Wi-Fi password in a preset
        self.assertNotIn("serial", saved)      # not a device
        settings.delete_preset("Продажа Польша")
        self.assertEqual(settings.load()["presets"], {})

    def test_empty_name_is_refused(self):
        self.assertIsNone(settings.save_preset("   ", {"language": "x"}))

    def test_limit(self):
        for i in range(settings.PRESET_MAX + 5):
            settings.save_preset(f"p{i}", {"language": "x"})
        self.assertLessEqual(len(settings.load()["presets"]), settings.PRESET_MAX)


if __name__ == "__main__":
    unittest.main()
