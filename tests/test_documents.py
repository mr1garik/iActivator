"""Tests for the service documents (intake/handover/warranty PDF). Run: python -m unittest discover tests"""
import importlib.util
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("HOME", tempfile.mkdtemp())
for _name in ("pymobiledevice3", "pymobiledevice3.usbmux", "pymobiledevice3.ca", "pymobiledevice3.exceptions",
              "pymobiledevice3.lockdown", "pymobiledevice3.services", "pymobiledevice3.services.diagnostics",
              "pymobiledevice3.services.mobile_activation", "pymobiledevice3.services.mobile_config",
              "cryptography", "cryptography.x509", "cryptography.hazmat", "cryptography.hazmat.primitives",
              "cryptography.hazmat.primitives.serialization", "keyring"):
    sys.modules.setdefault(_name, mock.MagicMock())
for _exc in ("CloudConfigurationAlreadyPresentError", "MobileActivationException", "ProfileError"):
    if not isinstance(getattr(sys.modules["pymobiledevice3.exceptions"], _exc, None), type):
        setattr(sys.modules["pymobiledevice3.exceptions"], _exc, type(_exc, (Exception,), {}))

HAVE = importlib.util.find_spec("fpdf")
DEV = {"id": "A", "serial": "HFMHQCMXP9", "model_name": "iPhone 13", "capacity": "128 ГБ",
       "imei": "351888566941038", "ios": "18.6", "battery": 92}
SHOP = {"name": "Сервис iFix", "phone": "+380 67 000 00 00", "address": "Киев", "warranty_months": 3}


@unittest.skipUnless(HAVE, "needs fpdf2 (installed in the build workflow)")
class Documents(unittest.TestCase):
    def setUp(self):
        for k in [k for k in sys.modules if k == "fpdf" or k.startswith("fpdf.")]:
            if isinstance(sys.modules[k], mock.MagicMock):
                sys.modules.pop(k)
        from iactivator import documents, i18n
        self.documents = documents
        i18n.set_lang("ru")
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        p = mock.patch.object(documents, "app_data_dir", return_value=self.dir)
        p.start(); self.addCleanup(p.stop)

    def test_three_kinds_build_a_pdf(self):
        for kind in ("intake", "handover", "warranty"):
            path = self.documents.build(kind, DEV, SHOP, {"number": "7", "customer": "Олег", "defects": "скол", "work": "экран", "price": "3500"})
            self.assertTrue(path.read_bytes().startswith(b"%PDF"))
            self.assertTrue(path.suffix == ".pdf" and path.stat().st_size > 1000)

    def test_warranty_months_default_from_shop(self):
        path = self.documents.build("warranty", DEV, SHOP, {})  # no months in fields -> shop's 3
        self.assertTrue(path.exists())

    def test_unknown_kind_refused(self):
        with self.assertRaises(ValueError):
            self.documents.build("nope", DEV, SHOP, {})


if __name__ == "__main__":
    unittest.main()
