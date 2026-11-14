"""Tests for repairing the "start with Windows" entry. Run: python -m unittest discover tests"""
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from iactivator import autostart  # noqa: E402


class FakeKey:
    def __enter__(self): return self
    def __exit__(self, *a): return False


def fake_winreg(store):
    def query(key, name):
        if name not in store:
            raise OSError("missing")
        return store[name], 1

    return types.SimpleNamespace(
        HKEY_CURRENT_USER=0, REG_SZ=1,
        OpenKey=lambda root, path: FakeKey(), CreateKey=lambda root, path: FakeKey(),
        QueryValueEx=lambda key, name: query(key, name),
        SetValueEx=lambda key, name, res, kind, value: store.__setitem__(name, value),
        DeleteValue=lambda key, name: store.pop(name))


class Repair(unittest.TestCase):
    def setUp(self):
        self.store = {}
        sys.modules["winreg"] = fake_winreg(self.store)
        self.addCleanup(sys.modules.pop, "winreg", None)
        self._orig = (autostart.supported, autostart._command)
        autostart.supported = lambda: True
        autostart._command = lambda: '"C:\\Users\\me\\AppData\\Local\\Programs\\iActivator\\iActivator.exe"'
        self.addCleanup(self.restore)

    def restore(self):
        autostart.supported, autostart._command = self._orig

    def test_entry_to_a_deleted_program_is_pointed_here(self):
        self.store["iActivator"] = '"C:\\Users\\Ігор\\Downloads\\iActivator.exe"'  # old portable, deleted
        self.assertTrue(autostart.repair())
        self.assertEqual(self.store["iActivator"], autostart._command())

    def test_entry_to_an_existing_copy_is_left_alone(self):
        existing = Path(tempfile.mkdtemp()) / "iActivator.exe"
        existing.write_bytes(b"MZ")
        self.store["iActivator"] = f'"{existing}"'
        self.assertFalse(autostart.repair())
        self.assertEqual(self.store["iActivator"], f'"{existing}"')

    def test_nothing_happens_when_start_up_is_off(self):
        self.assertFalse(autostart.repair())
        self.assertEqual(self.store, {})


if __name__ == "__main__":
    unittest.main()
