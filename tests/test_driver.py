"""Tests for the Windows Apple-driver check. Run: python -m unittest discover tests

The decisions (diagnose) and the scripts are tested here on any system; actually
running the scripts needs Windows with administrator rights.
"""
import base64
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from iactivator import driver  # noqa: E402

PHONE = {"name": "Apple Mobile Device USB Composite Device", "status": "OK", "class": "USB",
         "id": "USB\\VID_05AC&PID_12A8\\00008030001A2B3C4D5E6F70", "problem": "CM_PROB_NONE"}
PHONE_IFACE = {"name": "Apple iPhone", "status": "OK", "class": "WPD",
               "id": "USB\\VID_05AC&PID_12A8&MI_00\\6&1234&0&0000", "problem": "CM_PROB_NONE"}


def facts(**kw):
    base = {"windows": True, "service": "store", "state": "running", "mux": True, "mux_devices": 1,
            "usb": [PHONE, PHONE_IFACE]}
    base.update(kw)
    return base


class Diagnose(unittest.TestCase):
    def test_not_windows(self):
        r = driver.diagnose({"windows": False})
        self.assertEqual((r["level"], r["fix"]), ("ok", None))

    def test_no_apple_software(self):
        r = driver.diagnose(facts(service=None, state="missing", mux=False))
        self.assertEqual((r["code"], r["fix"]), ("no_driver", "install"))

    def test_service_stopped(self):
        r = driver.diagnose(facts(state="stopped", mux=False))
        self.assertEqual((r["code"], r["fix"]), ("service_stopped", "restart"))

    def test_service_running_but_not_answering(self):
        r = driver.diagnose(facts(mux=False))
        self.assertEqual((r["code"], r["fix"]), ("service_stopped", "restart"))

    def test_device_with_driver_error(self):
        broken = dict(PHONE, status="Error", problem="CM_PROB_FAILED_INSTALL")
        r = driver.diagnose(facts(usb=[broken]))
        self.assertEqual((r["code"], r["fix"]), ("device_driver_error", "reinstall"))
        self.assertIn("CM_PROB_FAILED_INSTALL", r["message"])

    def test_phone_seen_only_as_camera(self):
        # Windows' own driver works (status OK) but the Apple service sees no iPhone.
        generic = dict(PHONE, name="USB Composite Device")
        r = driver.diagnose(facts(usb=[generic, PHONE_IFACE], mux_devices=0))
        self.assertEqual((r["code"], r["fix"]), ("device_not_seen", "reinstall"))

    def test_all_good_with_phone(self):
        r = driver.diagnose(facts())
        self.assertEqual((r["level"], r["code"], r["fix"]), ("ok", "ok", None))

    def test_all_good_without_phone(self):
        r = driver.diagnose(facts(usb=[], mux_devices=0))
        self.assertEqual((r["level"], r["code"]), ("ok", "ok_no_device"))

    def test_unknown_service_device_count_is_not_blamed_on_the_driver(self):
        r = driver.diagnose(facts(mux_devices=None))
        self.assertEqual(r["fix"], None)

    def test_failed_usb_query_is_not_blamed_on_the_driver(self):
        r = driver.diagnose(facts(usb=None, mux_devices=0))
        self.assertEqual(r["fix"], None)

    def test_itunes_is_named(self):
        r = driver.diagnose(facts(service="itunes"))
        self.assertIn("iTunes", r["message"])


class Scripts(unittest.TestCase):
    def test_elevated_script_reports_into_the_result_file(self):
        path = Path("C:/Users/Игорь O'Neil/AppData/Local/Temp/x/result.txt")  # Cyrillic and a quote
        s = driver.build_elevated_script("Log 'hi'", path)
        self.assertIn("$out = 'C:/Users/Игорь O''Neil/AppData/Local/Temp/x/result.txt'", s)
        self.assertIn("RESULT: OK", s)
        self.assertIn("RESULT: ERROR", s)
        self.assertIn("$ErrorActionPreference = 'Stop'", s)

    def test_launcher_passes_the_script_encoded(self):
        script = driver.build_elevated_script(driver.REINSTALL_SCRIPT, Path("C:/Temp/Игорь/result.txt"))
        cmd = driver.build_launcher(script)
        self.assertEqual(cmd[0], "powershell")
        outer = cmd[-1]
        self.assertIn("-Verb RunAs", outer)
        self.assertIn("catch { exit 5 }", outer)
        b64 = re.search(r"'-EncodedCommand','([A-Za-z0-9+/=]+)'", outer).group(1)
        self.assertEqual(base64.b64decode(b64).decode("utf-16-le"), script)  # round-trips, Cyrillic included
        self.assertLess(len(outer), 30000)  # Windows command-line limit is 32767

    def test_scripts_have_balanced_braces_and_quotes(self):
        for name in ("RESTART_SCRIPT", "REINSTALL_SCRIPT"):
            s = getattr(driver, name)
            with self.subTest(name):
                self.assertEqual(s.count("{"), s.count("}"))
                self.assertEqual(s.count("("), s.count(")"))
                no_escaped = s.replace("''", "")
                self.assertEqual(no_escaped.count("'") % 2, 0)

    def test_reinstall_script_targets_apple_mobile_devices_only(self):
        s = driver.REINSTALL_SCRIPT
        self.assertIn("'USB\\VID_05AC&PID_12*'", s)
        self.assertIn("usbaapl64.inf", s)
        self.assertIn("pnputil /add-driver", s)
        self.assertIn("pnputil /scan-devices", s)
        self.assertNotIn("Remove-Item", s)  # deletes no files

    def test_restart_does_not_stop_on_startup_type(self):
        self.assertIn("-StartupType Automatic -ErrorAction SilentlyContinue", driver.RESTART_SCRIPT)


if __name__ == "__main__":
    unittest.main()
