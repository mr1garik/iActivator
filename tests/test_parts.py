"""Tests for the replaced-parts check. Run: python -m unittest discover tests"""
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

from iactivator import core, history, i18n  # noqa: E402

FIRST = {"BatterySerialNumber": "F5D9381ABCDQ0", "PanelSerialNumber": "C0D93820XYZ1",
         "RearFacingCameraModuleSerialNumber": "DN89381QWERTY"}


def check(current, baseline=None, since="01.11.2026"):
    (c,) = core.parts_checks(current, baseline, since)
    return c["status"], c["detail"]


class PartsCheck(unittest.TestCase):
    def setUp(self):
        i18n.set_lang("ru")
        self.addCleanup(i18n.set_lang, "ru")

    def test_first_check_records(self):
        status, detail = check(FIRST)
        self.assertEqual(status, "info")
        self.assertIn("Батарея", detail)
        self.assertNotIn("F5D9381ABCDQ0", detail)  # serial numbers are never shown

    def test_unchanged(self):
        status, detail = check(FIRST, FIRST)
        self.assertEqual(status, "ok")
        self.assertIn("01.11.2026", detail)

    def test_replaced_battery(self):
        status, detail = check(dict(FIRST, BatterySerialNumber="F5D0000NEW000"), FIRST)
        self.assertEqual(status, "bad")
        self.assertIn("Батарея", detail)
        self.assertNotIn("Дисплей", detail)

    def test_nothing_readable(self):
        self.assertEqual(check({})[0], "info")

    def test_nothing_in_common_with_the_reference(self):
        status, _ = check({"MesaSerialNumber": "ABCDEF123"}, {"PanelSerialNumber": "C0D93820XYZ1"})
        self.assertEqual(status, "info")

    def test_english(self):
        i18n.set_lang("en")
        self.assertEqual(check(dict(FIRST, PanelSerialNumber="NEWPANEL0001"), FIRST),
                         ("bad", "Replaced since the check on 01.11.2026: Display"))


class ReadingSerials(unittest.TestCase):
    def test_serial_text(self):
        self.assertEqual(core._serial_text(" F5D9381ABCDQ0 "), "F5D9381ABCDQ0")
        self.assertEqual(core._serial_text(b"F5D9381ABCDQ0"), "F5D9381ABCDQ0")
        self.assertEqual(core._serial_text(b"\x01\x02\x03\x04\x05\x06"), "010203040506")
        self.assertIsNone(core._serial_text("0000000000"))
        self.assertIsNone(core._serial_text("abc"))
        self.assertIsNone(core._serial_text(None))

    def test_battery_serial_from_ioregistry(self):
        self.assertEqual(core.battery_serial({"Serial": "F5D9381ABCDQ0"}), "F5D9381ABCDQ0")
        self.assertEqual(core.battery_serial({"BatteryData": {"Serial": "F5D9381ABCDQ0"}}), "F5D9381ABCDQ0")
        self.assertIsNone(core.battery_serial({}))

    def _read(self, mobilegestalt, battery_raw):
        class Diag:
            async def __aenter__(self): return self
            async def __aexit__(self, *a): return False
            async def mobilegestalt(self, keys): return mobilegestalt(keys)
        orig = core.DiagnosticsService
        core.DiagnosticsService = lambda lockdown: Diag()
        try:
            return asyncio.run(core.read_part_serials(object(), battery_raw))
        finally:
            core.DiagnosticsService = orig

    def test_old_ios_reports_parts(self):
        got = self._read(lambda keys: {"BatterySerialNumber": "F5D9381ABCDQ0", "PanelSerialNumber": "C0D93820XYZ1",
                                       "MesaSerialNumber": "", "Status": "Success"}, None)
        self.assertEqual(got, {"BatterySerialNumber": "F5D9381ABCDQ0", "PanelSerialNumber": "C0D93820XYZ1"})

    def test_new_ios_falls_back_to_the_battery(self):
        def deprecated(keys):
            raise RuntimeError("MobileGestalt is deprecated on iOS 17.4 and later")
        got = self._read(deprecated, {"BatteryData": {"Serial": "F5D9381ABCDQ0"}})
        self.assertEqual(got, {"BatterySerialNumber": "F5D9381ABCDQ0"})


class Reference(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self._orig = (history.json_path, history.csv_path)
        history.json_path = lambda: self.dir / "history.json"
        history.csv_path = lambda: self.dir / "history.csv"
        history._reset_cache()
        self.addCleanup(self.restore)

    def restore(self):
        history.flush_csv()
        history.json_path, history.csv_path = self._orig
        history._reset_cache()

    def test_reference_is_kept_after_a_replacement(self):
        self.assertEqual(history.parts_baseline("U1"), (None, None))
        history.record_parts("U1", FIRST)
        ref, when = history.parts_baseline("U1")
        self.assertEqual(ref, FIRST)
        self.assertTrue(when)
        history.record_parts("U1", dict(FIRST, BatterySerialNumber="F5D0000NEW000", MesaSerialNumber="ABCDEF123"))
        ref, _ = history.parts_baseline("U1")
        self.assertEqual(ref["BatterySerialNumber"], "F5D9381ABCDQ0")  # not overwritten
        self.assertEqual(ref["MesaSerialNumber"], "ABCDEF123")         # newly readable part added
        history._reset_cache()
        self.assertEqual(history.parts_baseline("U1")[0]["BatterySerialNumber"], "F5D9381ABCDQ0")


if __name__ == "__main__":
    unittest.main()
