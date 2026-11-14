"""Tests for the self-update safety checks. Run: python -m unittest discover tests"""
import hashlib
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("HOME", tempfile.mkdtemp())
os.environ.setdefault("APPDATA", os.environ["HOME"])
# The updater itself needs none of the device libraries; stub them so the tests run anywhere.
for _name in ("pymobiledevice3", "pymobiledevice3.usbmux", "pymobiledevice3.ca", "pymobiledevice3.exceptions",
              "pymobiledevice3.lockdown", "pymobiledevice3.services", "pymobiledevice3.services.diagnostics",
              "pymobiledevice3.services.mobile_activation", "pymobiledevice3.services.mobile_config",
              "cryptography", "cryptography.x509", "cryptography.hazmat", "cryptography.hazmat.primitives",
              "cryptography.hazmat.primitives.serialization"):
    sys.modules.setdefault(_name, MagicMock())
for _exc in ("CloudConfigurationAlreadyPresentError", "MobileActivationException", "ProfileError"):
    setattr(sys.modules["pymobiledevice3.exceptions"], _exc, type(_exc, (Exception,), {}))

from iactivator import update  # noqa: E402

BIG = update.MIN_UPDATE_BYTES + 1024


class VerifyDownload(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    def exe(self, body: bytes) -> Path:
        p = self.dir / update.ASSET_WINDOWS
        p.write_bytes(body)
        return p

    def zip(self, with_app=True, size=BIG) -> Path:
        p = self.dir / update.ASSET_MACOS
        with zipfile.ZipFile(p, "w", zipfile.ZIP_STORED) as z:
            z.writestr("iActivator.app/Contents/MacOS/iActivator" if with_app else "readme.txt", b"x" * size)
        return p

    def test_good_exe_passes(self):
        body = b"MZ" + b"\0" * BIG
        p = self.exe(body)
        update._verify_download(p, len(body), "sha256:" + hashlib.sha256(body).hexdigest())

    def test_no_size_or_digest_from_github_still_passes(self):
        update._verify_download(self.exe(b"MZ" + b"\0" * BIG), None, None)

    def test_truncated_download_is_refused(self):
        body = b"MZ" + b"\0" * BIG
        with self.assertRaises(update.UpdateError):
            update._verify_download(self.exe(body[: len(body) // 2]), len(body), None)

    def test_tiny_file_is_refused(self):
        with self.assertRaises(update.UpdateError):
            update._verify_download(self.exe(b"MZ<html>error</html>"), None, None)

    def test_wrong_checksum_is_refused(self):
        body = b"MZ" + b"\0" * BIG
        with self.assertRaises(update.UpdateError):
            update._verify_download(self.exe(body), len(body), "sha256:" + "0" * 64)

    def test_not_a_windows_program_is_refused(self):
        with self.assertRaises(update.UpdateError):
            update._verify_download(self.exe(b"PK" + b"\0" * BIG), None, None)

    def test_good_zip_passes(self):
        update._verify_download(self.zip(), None, None)

    def test_zip_without_app_is_refused(self):
        with self.assertRaises(update.UpdateError):
            update._verify_download(self.zip(with_app=False), None, None)

    def test_broken_zip_is_refused(self):
        p = self.zip()
        data = p.read_bytes()
        p.write_bytes(data[: len(data) - 4000])
        with self.assertRaises(update.UpdateError):
            update._verify_download(p, None, None)


class WindowsHelper(unittest.TestCase):
    def test_script_is_plain_ascii_without_paths(self):
        update._WIN_HELPER.encode("ascii")  # no user paths inside, so no code-page trouble
        self.assertIn('move /y "%~1" "%~2"', update._WIN_HELPER)
        self.assertNotIn("timeout", update._WIN_HELPER)  # does not work in a detached process
        self.assertIn("if %N% lss 60 goto wait", update._WIN_HELPER)  # the retry loop is bounded


@unittest.skipIf(sys.platform == "win32" or not shutil.which("bash"), "needs bash")
class MacHelper(unittest.TestCase):
    """Run the real helper script with stand-ins for the macOS-only tools."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="обновление тест "))  # spaces and Cyrillic on purpose
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.bin = self.dir / "bin"
        self.bin.mkdir()
        self.tool("ditto", 'cp -R "$1" "$2"')
        self.tool("xattr", "exit 0")
        self.tool("open", 'echo "$1" > "%s"' % (self.dir / "opened"))
        self.app = self.dir / "Programs" / "iActivator.app"
        self.new = self.dir / "extracted" / "iActivator.app"
        self.backup = self.dir / "data" / "previous-version" / "iActivator.app"
        for d, version in ((self.app, "old"), (self.new, "new")):
            d.mkdir(parents=True)
            (d / "version").write_text(version)
        self.backup.parent.mkdir(parents=True)
        self.helper = self.dir / "update.sh"
        self.helper.write_text(update._MAC_HELPER)

    def tool(self, name: str, body: str) -> None:
        p = self.bin / name
        p.write_text("#!/bin/bash\n" + body + "\n")
        p.chmod(p.stat().st_mode | stat.S_IEXEC)

    def run_helper(self):
        env = dict(os.environ, PATH=f"{self.bin}{os.pathsep}{os.environ['PATH']}")
        subprocess.run(["bash", str(self.helper), "999999", str(self.new), str(self.app), str(self.backup)],
                       env=env, check=True, timeout=30)

    def test_update_replaces_app_and_keeps_previous_version(self):
        self.run_helper()
        self.assertEqual((self.app / "version").read_text(), "new")
        self.assertEqual((self.backup / "version").read_text(), "old")
        self.assertFalse(Path(str(self.app) + ".new").exists())
        self.assertEqual((self.dir / "opened").read_text().strip(), str(self.app))

    def test_failed_copy_leaves_the_old_app_working(self):
        self.tool("ditto", "exit 1")
        self.run_helper()
        self.assertEqual((self.app / "version").read_text(), "old")
        self.assertEqual((self.dir / "opened").read_text().strip(), str(self.app))

    def test_old_backup_is_replaced_by_the_latest_one(self):
        self.backup.mkdir()
        (self.backup / "version").write_text("ancient")
        self.run_helper()
        self.assertEqual((self.backup / "version").read_text(), "old")


class ReleaseNames(unittest.TestCase):
    def test_names_differ_from_the_ones_v3_0_looks_for(self):
        # v3.0's installer must never find these files (see update.ASSET_* comment).
        self.assertNotIn(update.ASSET_WINDOWS, ("iActivator.exe", "iActivator-mac.zip"))
        self.assertNotIn(update.ASSET_MACOS, ("iActivator.exe", "iActivator-mac.zip"))
        workflow = (ROOT / ".github" / "workflows" / "build.yml").read_text()
        self.assertIn(update.ASSET_WINDOWS, workflow)
        self.assertIn(update.ASSET_MACOS, workflow)


@unittest.skipIf(sys.platform == "win32" or not shutil.which("zip") or not shutil.which("unzip"), "needs zip/unzip")
class ExtractedApp(unittest.TestCase):
    """The v3.0 bug: Python's zipfile drops the executable flag, so the updated app cannot start."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        app = self.dir / "src" / "iActivator.app"
        (app / "Contents" / "MacOS").mkdir(parents=True)
        main = app / "Contents" / "MacOS" / "iActivator"
        main.write_bytes(b"\xcf\xfa\xed\xfe")
        main.chmod(0o755)
        (app / "Contents" / "Frameworks").mkdir()
        os.symlink("../MacOS/iActivator", app / "Contents" / "Frameworks" / "link")
        self.zip = self.dir / update.ASSET_MACOS
        subprocess.run(["zip", "-qry", str(self.zip), "iActivator.app"], cwd=app.parent, check=True)

    def test_python_extraction_is_refused(self):
        out = self.dir / "py"
        with zipfile.ZipFile(self.zip) as z:
            z.extractall(out)
        with self.assertRaises(update.UpdateError):
            update._check_extracted_app(out)

    def test_extraction_that_keeps_permissions_is_accepted(self):
        out = self.dir / "unz"
        subprocess.run(["unzip", "-q", str(self.zip), "-d", str(out)], check=True)  # keeps flags like ditto
        app = update._check_extracted_app(out)
        self.assertEqual(app.name, "iActivator.app")
        self.assertTrue((app / "Contents" / "Frameworks" / "link").is_symlink())

    def test_archive_without_app_is_refused(self):
        with self.assertRaises(update.UpdateError):
            update._check_extracted_app(self.dir / "empty-folder-does-not-exist")


if __name__ == "__main__":
    unittest.main()
