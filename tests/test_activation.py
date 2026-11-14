"""Tests for the legacy (iOS < 10) activation helpers. Run: python -m unittest discover tests"""
import os
import plistlib
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

RECORD = {"AccountToken": b"token", "FairPlayKeyData": b"key", "DeviceCertificate": b"cert"}


class LegacyActivation(unittest.TestCase):
    def test_ios_major(self):
        self.assertEqual(core.ios_major("7.1.2"), 7)
        self.assertEqual(core.ios_major("9.3.6"), 9)
        self.assertEqual(core.ios_major("18.1"), 18)
        self.assertEqual(core.ios_major(None), 0)
        self.assertEqual(core.ios_major("?"), 0)

    def test_old_devices_take_the_legacy_path(self):
        legacy = lambda v: 0 < core.ios_major(v) < core.LEGACY_ACTIVATION_BELOW_IOS  # noqa: E731
        self.assertTrue(legacy("7.1.2"))   # iPhone 4
        self.assertTrue(legacy("9.3.6"))   # iPhone 4S
        self.assertFalse(legacy("10.3.4"))
        self.assertFalse(legacy("17.5"))
        self.assertFalse(legacy("?"))      # unknown version: keep the normal path

    def test_record_from_plain_plist(self):
        reply = plistlib.dumps({"iphone-activation": {"activation-record": RECORD, "ack-received": True}})
        self.assertEqual(core.extract_activation_record(reply), RECORD)

    def test_record_under_device_activation(self):
        reply = plistlib.dumps({"device-activation": {"activation-record": RECORD}})
        self.assertEqual(core.extract_activation_record(reply), RECORD)

    def test_record_embedded_in_html(self):
        plist = plistlib.dumps({"iphone-activation": {"activation-record": RECORD}})
        html = (b'<html><body><script id="protocol" type="text/x-apple-plist">'
                + plist[plist.index(b"<plist"):] + b"</script></body></html>")
        self.assertEqual(core.extract_activation_record(html), RECORD)

    def test_no_record(self):
        self.assertIsNone(core.extract_activation_record(plistlib.dumps({"iphone-activation": {"ack-received": True}})))
        self.assertIsNone(core.extract_activation_record(b"<html>Your request could not be completed</html>"))
        self.assertIsNone(core.extract_activation_record(b""))


if __name__ == "__main__":
    unittest.main()
