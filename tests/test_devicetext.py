"""Tests for the per-phone TXT files and clearing them. Run: python -m unittest discover tests"""
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
              "cryptography.hazmat.primitives.serialization"):
    sys.modules.setdefault(_name, mock.MagicMock())
for _exc in ("CloudConfigurationAlreadyPresentError", "MobileActivationException", "ProfileError"):
    if not isinstance(getattr(sys.modules["pymobiledevice3.exceptions"], _exc, None), type):
        setattr(sys.modules["pymobiledevice3.exceptions"], _exc, type(_exc, (Exception,), {}))

from iactivator import devicetext, history, i18n  # noqa: E402

PHONE = {"id": "00008130-001A2B3C4D5E6F70", "serial": "DN9210F22M", "model": "iPhone16,2",
         "model_name": "iPhone 15 Pro Max", "capacity": "256 ГБ", "imei": "356789012345678", "ios": "27.2",
         "battery": 83, "activation": "Unactivated", "first_seen": "2026-11-14 16:51:03",
         "last_seen": "2026-11-14 16:51:03",
         "parts": {"time": "2026-11-14 16:51:03", "serials": {"BatterySerialNumber": "F5D1234"}},
         "events": [{"time": "2026-11-14 16:51:03", "action": "Подключение", "result": "info",
                     "detail": "не активирован"},
                    {"time": "2026-11-14 16:52:00", "action": "Активация", "result": "ok", "detail": ""}]}


class DeviceText(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        for target in ("iactivator.devicetext.app_data_dir", "iactivator.history.app_data_dir"):
            p = mock.patch(target, return_value=self.dir)
            p.start(); self.addCleanup(p.stop)
        self.reports = self.dir / "Отчёты"
        self.reports.mkdir()
        history._reset_cache()
        self.addCleanup(history._reset_cache)
        with history._lock:
            history._load()[PHONE["id"]] = dict(PHONE)
        i18n.set_lang("ru")
        self.addCleanup(i18n.set_lang, "ru")

    def test_text_has_the_facts_parts_and_events(self):
        s = devicetext.render(PHONE)
        self.assertRegex(s, r"Активация: +не активирован")
        for part in ("iPhone 15 Pro Max, 256 ГБ", "DN9210F22M", "356789012345678", "83%",
                     "Батарея: F5D1234", "Батарея (здоровье): 83%", "✓ Активация", "· Подключение: не активирован"):
            self.assertIn(part, s)

    def test_text_follows_the_language(self):
        i18n.set_lang("en")
        s = devicetext.render(PHONE)
        self.assertIn("256 GB", s)
        self.assertIn("Last seen", s)

    def test_one_small_file_per_phone_saved_again_in_place(self):
        other = dict(PHONE, id="X" * 25, serial="F17ABC/12", model_name="iPhone 12")
        with history._lock:
            history._load()[other["id"]] = other
        paths = devicetext.save()
        self.assertEqual(sorted(p.name for p in paths), ["iPhone 12 F17ABC 12.txt", "iPhone 15 Pro Max DN9210F22M.txt"])
        self.assertTrue(all(p.stat().st_size < 4096 for p in paths))
        self.assertEqual(devicetext.save([PHONE["id"]]), [paths[1]] if "15" in paths[1].name else [paths[0]])
        self.assertEqual(len(list(devicetext.texts_dir().iterdir())), 2)  # overwritten, not copied
        self.assertTrue(paths[0].read_bytes().startswith(b"\xef\xbb\xbf"))  # Notepad reads Cyrillic

    def test_unknown_device_saves_nothing(self):
        self.assertEqual(devicetext.save(["nope"]), [])

    def test_clear_removes_only_txt_and_pdf_and_keeps_the_history(self):
        devicetext.save()
        (self.reports / "report.pdf").write_bytes(b"%PDF" + b"0" * 5000)
        keep = self.reports / "notes.docx"
        keep.write_bytes(b"x")
        u = devicetext.usage()
        self.assertEqual(u["files"], 2)
        r = devicetext.clear_files()
        self.assertEqual((r["removed"], r["bytes"]), (2, u["bytes"]))
        self.assertEqual(devicetext.usage()["files"], 0)
        self.assertTrue(keep.exists())
        self.assertIn(PHONE["id"], history.export())  # files can be made again

    def test_clear_with_nothing_there(self):
        self.assertEqual(devicetext.clear_files()["removed"], 0)


if __name__ == "__main__":
    unittest.main()
