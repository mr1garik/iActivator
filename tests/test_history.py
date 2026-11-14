"""Tests for the device history and the in-memory journal. Run: python -m unittest discover tests"""
import csv
import json
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

from iactivator import applog, history  # noqa: E402


class History(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self._orig = (history.json_path, history.csv_path)
        history.json_path = lambda: self.dir / "history.json"
        history.csv_path = lambda: self.dir / "history.csv"
        history._reset_cache()
        self.addCleanup(self.restore)

    def restore(self):
        history.flush_csv()  # stop the pending timer before the folder goes away
        history.json_path, history.csv_path = self._orig
        history._reset_cache()

    def test_events_are_saved_to_the_file_right_away(self):
        history.update_device({"conn_id": "U1", "serial": "S1", "model": "iPhone12,8", "model_name": "iPhone SE"})
        history.add_event("U1", "Активация", "ok", "")
        on_disk = json.loads((self.dir / "history.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk["U1"]["events"][0]["action"], "Активация")
        history._reset_cache()  # like a restart
        self.assertEqual(history.summary()["devices"][0]["serial"], "S1")

    def test_the_file_is_not_re_read_for_every_event(self):
        history.add_event("U1", "Подключение", "info", "")
        (self.dir / "history.json").write_text("not json", encoding="utf-8")  # would wipe it if re-read
        history.add_event("U1", "Активация", "ok", "")
        on_disk = json.loads((self.dir / "history.json").read_text(encoding="utf-8"))
        self.assertEqual([e["action"] for e in on_disk["U1"]["events"]], ["Подключение", "Активация"])

    def test_csv_is_written_later_and_on_flush(self):
        history.add_event("U1", "Активация", "ok", "x")
        self.assertFalse((self.dir / "history.csv").exists())
        history.flush_csv()
        with open(self.dir / "history.csv", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f, delimiter=";"))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][7], "Активация")

    def test_csv_is_rebuilt_at_start_when_missing(self):
        history.add_event("U1", "Активация", "ok", "")
        history.flush_csv()
        (self.dir / "history.csv").unlink()
        history._reset_cache()
        history.summary()          # first read after a restart notices the missing table
        history.flush_csv()
        self.assertTrue((self.dir / "history.csv").exists())

    def test_summary_is_a_copy(self):
        history.add_event("U1", "Активация", "ok", "")
        s = history.summary()
        s["devices"][0]["events"].clear()
        self.assertEqual(len(history.summary()["devices"][0]["events"]), 1)
        self.assertEqual(history.summary()["stats"]["activated"], 1)

    def test_merge_and_delete(self):
        history.add_event("U1", "Активация", "ok", "")
        other = {"U2": {"id": "U2", "model": "iPhone14,5", "events": [{"time": "2026-01-01 10:00:00",
                                                                        "action": "Диагностика", "result": "ok"}]}}
        self.assertEqual(history.merge(other), 1)
        self.assertEqual(history.summary()["stats"]["total"], 2)
        history.delete("U2")
        self.assertEqual(history.summary()["stats"]["total"], 1)
        history._reset_cache()
        self.assertEqual(history.summary()["stats"]["total"], 1)


class Journal(unittest.TestCase):
    def setUp(self):
        self._saved = (applog.MAX_IN_MEMORY, applog.KEEP_AFTER_TRIM, list(applog._entries), applog._dropped)
        applog.MAX_IN_MEMORY, applog.KEEP_AFTER_TRIM = 10, 6
        applog._entries.clear()
        applog._dropped = 0
        self.addCleanup(self.restore)

    def restore(self):
        applog.MAX_IN_MEMORY, applog.KEEP_AFTER_TRIM, entries, applog._dropped = self._saved
        applog._entries[:] = entries

    def test_memory_is_capped_and_positions_stay_valid(self):
        _, pos = applog.since(0)
        for i in range(8):
            applog.add(f"line {i}")
        got, pos = applog.since(pos)
        self.assertEqual([e["text"] for e in got], [f"line {i}" for i in range(8)])
        for i in range(8, 25):
            applog.add(f"line {i}")
        self.assertLessEqual(len(applog._entries), applog.MAX_IN_MEMORY)
        got, new_pos = applog.since(pos)       # the window asks for what came after line 7
        self.assertEqual(got[-1]["text"], "line 24")
        self.assertEqual(new_pos, 25)
        self.assertNotIn("line 7", [e["text"] for e in got])
        got, _ = applog.since(new_pos)
        self.assertEqual(got, [])


if __name__ == "__main__":
    unittest.main()
