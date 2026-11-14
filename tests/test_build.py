"""The packages build.py leaves out of the app must never be needed by it.

Runs the app's imports in a clean Python process (with the real libraries, as in the
build workflow) and checks that none of the excluded packages gets loaded.
Run: python -m unittest discover tests
"""
import importlib.metadata
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build  # noqa: E402

PROBE = r"""
import json, os, sys, tempfile
os.environ.setdefault("HOME", tempfile.mkdtemp())
os.environ.setdefault("APPDATA", os.environ["HOME"])
sys.path.insert(0, sys.argv[1])
from iactivator import webui, core, update, report, driver, history, settings, applog
import pymobiledevice3.services.crash_reports
print(json.dumps(sorted({m.split(".")[0] for m in sys.modules})))
"""


def _real(dist):
    """Installed? (Asked by distribution: other test files replace these modules with stubs.)"""
    try:
        importlib.metadata.distribution(dist)
        return True
    except importlib.metadata.PackageNotFoundError:
        return False


@unittest.skipUnless(_real("pymobiledevice3") and _real("keyring") and _real("fpdf2"),
                     "needs the app's libraries (installed in the build workflow)")
class Exclusions(unittest.TestCase):
    def test_the_app_never_loads_an_excluded_package(self):
        out = subprocess.run([sys.executable, "-c", PROBE, str(ROOT)], capture_output=True, text=True,
                             timeout=300, cwd=str(ROOT))
        self.assertEqual(out.returncode, 0, out.stderr[-2000:])
        loaded = set(json.loads(out.stdout.strip().splitlines()[-1]))
        self.assertEqual(sorted(loaded & set(build.EXCLUDES)), [])


class Options(unittest.TestCase):
    def test_every_platform_gets_the_exclusions_and_the_page(self):
        for platform in ("win32", "darwin"):
            with self.subTest(platform):
                args = build.pyinstaller_args(platform=platform)
                self.assertEqual(args.count("--exclude-module"), len(build.EXCLUDES))
                self.assertTrue(any(a.startswith("iactivator/page.html") for a in args))
                self.assertEqual(args[-1], "main.py")
        self.assertIn("--onefile", build.pyinstaller_args(platform="win32"))
        self.assertNotIn("--onefile", build.pyinstaller_args(platform="darwin"))  # .app bundle

    def test_needed_packages_are_never_excluded(self):
        needed = {"pymobiledevice3", "cryptography", "requests", "keyring", "fpdf", "fontTools", "certifi",
                  "webview", "pystray", "PIL", "win32security", "clr_loader", "pythonnet", "typer", "rich",
                  "questionary", "prompt_toolkit", "pygments", "click", "pycrashreport"}
        self.assertEqual(sorted(needed & set(build.EXCLUDES)), [])


if __name__ == "__main__":
    unittest.main()
