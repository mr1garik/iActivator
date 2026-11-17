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


import importlib.util  # noqa: E402
import shutil  # noqa: E402
from unittest import mock  # noqa: E402

from iactivator import i18n  # noqa: E402

HAVE_LIBS = all(importlib.util.find_spec(m) for m in ("fpdf", "segno"))
PHONE = {"id": "A", "serial": "HFMHQCMXP9", "model_name": "iPhone 18 Pro", "capacity": "512 ГБ",
         "imei": "351888566941038", "ios": "27.0.1", "battery": 102, "last_seen": "2026-11-17 12:00:00",
         "note": "Цена 1200$", "events": [{"action": "Диагностика", "result": "warn"}]}


@unittest.skipUnless(HAVE_LIBS, "needs fpdf2 and segno (installed in the build workflow)")
class Labels(unittest.TestCase):
    def setUp(self):
        # Other test files replace fpdf with a stand-in; load the real one for these tests.
        import importlib
        saved = {k: sys.modules.pop(k) for k in ("fpdf", "iactivator.labels", "iactivator.report") if k in sys.modules}
        def restore():
            for k in ("fpdf", "iactivator.labels", "iactivator.report"):
                sys.modules.pop(k, None)
            sys.modules.update(saved)
        self.addCleanup(restore)
        for k in [k for k in sys.modules if k.startswith("fpdf.")]:
            sys.modules.pop(k)
        labels = importlib.import_module("iactivator.labels")
        self.labels = labels
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        p = mock.patch.object(labels, "app_data_dir", return_value=self.dir)
        p.start(); self.addCleanup(p.stop)
        i18n.set_lang("ru")

    def test_settings_keep_only_allowed_values(self):
        o = self.labels.options({"labels": {"enabled": True, "size": "99x99", "qr": "serial", "note": "yes",
                                            "show": {"imei": False, "hack": True, "serial": "no"},
                                            "field": "  Склад \n " + "x" * 50, "footer": 7}})
        self.assertEqual({k: o[k] for k in ("enabled", "size", "qr", "note")},
                         {"enabled": True, "size": "40x30", "qr": "serial", "note": False})
        self.assertEqual(o["show"], {**self.labels.DEFAULT_LINES, "imei": False})
        self.assertEqual(len(o["field"]), self.labels.FIELD_MAX)
        self.assertTrue(o["field"].startswith("Склад x"))
        self.assertEqual(o["footer"], "7")
        self.assertFalse(self.labels.options({})["enabled"])  # off until turned on in Settings

    def test_qr_content(self):
        self.assertEqual(self.labels.qr_text(PHONE, "serial"), "HFMHQCMXP9")
        text = self.labels.qr_text(PHONE, "text")
        for part in ("iPhone 18 Pro 512 ГБ", "S/N: HFMHQCMXP9", "IMEI: 351888566941038", "Батарея: 100%", "Годен с замечаниями"):
            self.assertIn(part, text)
        self.assertNotIn("Цена", text)  # the note is never in the QR code

    def test_note_only_when_asked(self):
        self.assertNotIn(("Цена 1200$", False), self.labels.lines_for(PHONE, False))
        self.assertIn(("Цена 1200$", False), self.labels.lines_for(PHONE, True))

    def test_template_field_name_lines_and_footer(self):
        opts = self.labels.options({"labels": {"note": True, "field": "Склад", "footer": "Магазин iFix",
                                               "show": {"imei": False, "battery": False, "date": False}}})
        rows = [t for t, _ in self.labels.lines_for(dict(PHONE, note="A-12"), opts)]
        self.assertEqual(rows, ["iPhone 18 Pro · 512 ГБ", "S/N HFMHQCMXP9", "Годен с замечаниями",
                                "Склад: A-12", "Магазин iFix"])

    def test_nothing_chosen_still_prints_the_serial(self):
        opts = self.labels.options({"labels": {"show": {k: False for k in self.labels.DEFAULT_LINES}}})
        self.assertEqual(self.labels.lines_for(PHONE, opts), [("HFMHQCMXP9", False)])

    def test_preview_is_one_sticker_laid_out_as_printed(self):
        opts = self.labels.options({"labels": {"size": "a4", "note": True, "field": "Склад"}})
        p = self.labels.preview(opts)
        self.assertEqual((p["w"], p["h"]), self.labels.SIZES["a4"])  # one sticker, not the sheet
        self.assertIn("Склад: A-12", [ln["text"] for ln in p["lines"]])
        m = p["qr"]["matrix"]
        self.assertEqual(len(m), len(m[0]))
        self.assertTrue(all(ln["x"] + ln["w"] <= p["w"] for ln in p["lines"]))
        self.assertTrue(all(ln["y"] + ln["h"] <= p["h"] + 0.01 for ln in p["lines"]))
        self.assertFalse((self.dir / "Наклейки").exists())  # nothing saved

    def test_never_checked_phone_has_no_verdict(self):
        self.assertEqual(self.labels.verdict(dict(PHONE, events=[])), "")

    def test_page_is_the_label_size(self):
        from fpdf import FPDF  # noqa: F401
        path = self.labels.build([PHONE, PHONE], {"size": "58x40", "qr": "text", "note": True})
        data = path.read_bytes()
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertEqual(data.count(b"/Type /Page\n") + data.count(b"/Type /Page>>") + data.count(b"/Type /Page "), 2)
        self.assertIn(b"164.41", data)  # 58 mm = 164.41 pt page width
        self.assertTrue(path.name.startswith("Наклейки "))

    def test_a4_sheet_holds_24(self):
        path = self.labels.build([PHONE] * 30, {"size": "a4", "qr": "serial", "note": False})
        data = path.read_bytes()
        self.assertIn(b"595.28", data)  # A4 width in points
        self.assertEqual(data.count(b"/Type /Page\n") + data.count(b"/Type /Page>>") + data.count(b"/Type /Page "), 2)

    def test_long_text_wraps_inside_a_small_label(self):
        _Labels, _layout = self.labels._Labels, self.labels._layout
        pdf = _Labels("40x30")
        pdf.add_page()
        size, lines = _layout(pdf, self.labels.lines_for(dict(PHONE, note="очень длинная заметка " * 3), True), 18, 26)
        self.assertTrue(all(pdf.get_string_width(t) <= 18.01 for t, _ in lines if not pdf.set_font("ui", "B" if _ else "", size)))


if __name__ == "__main__":
    unittest.main()
