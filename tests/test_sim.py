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

from iactivator import core, i18n  # noqa: E402

ICCID = "8938001234567891234"
PHONE = {"TelephonyCapability": True, "SIMStatus": "kCTSIMSupportSIMStatusReady",
         "SIMTrayStatus": "kCTSIMSupportSIMTrayInsertedWithSIM", "IntegratedCircuitCardIdentity": ICCID,
         "MobileSubscriberCountryCode": "255", "MobileSubscriberNetworkCode": "03",
         "CarrierBundleInfoArray": [{"CFBundleIdentifier": "com.apple.Kyivstar_ua", "CFBundleVersion": "60.0"}]}


def sim(**changes):
    v = dict(PHONE)
    for k, val in changes.items():
        if val is None:
            v.pop(k, None)
        else:
            v[k] = val
    return {c["name"]: (c["status"], c["detail"]) for c in core.sim_checks(v)}


class SimCheck(unittest.TestCase):
    def setUp(self):
        i18n.set_lang("ru")
        self.addCleanup(i18n.set_lang, "ru")

    def test_working_sim_shows_carrier_and_hides_iccid(self):
        r = sim()
        self.assertEqual(r["SIM-карта"][0], "ok")
        self.assertIn("Kyivstar", r["SIM-карта"][1])
        self.assertIn("…1234", r["SIM-карта"][1])
        self.assertNotIn(ICCID, r["SIM-карта"][1])
        self.assertEqual(r["Привязка к оператору"][0], "info")  # cannot be proven over USB

    def test_carrier_falls_back_to_mcc_mnc(self):
        r = sim(CarrierBundleInfoArray=None)
        self.assertIn("MCC 255 / MNC 03", r["SIM-карта"][1])

    def test_no_sim(self):
        r = sim(SIMStatus="kCTSIMSupportSIMStatusNotInserted", IntegratedCircuitCardIdentity=None)
        self.assertEqual(r["SIM-карта"], ("info", "Не вставлена"))

    def test_ready_without_iccid_is_treated_as_no_sim(self):
        r = sim(IntegratedCircuitCardIdentity=None, SIMTrayStatus=None)
        self.assertEqual(r["SIM-карта"][0], "info")

    def test_carrier_lock_is_reported(self):
        for status in ("OperatorLocked", "NetworkLocked", "ServiceProviderLocked"):
            with self.subTest(status):
                r = sim(SIMStatus="kCTSIMSupportSIMStatus" + status)
                self.assertEqual(r["SIM-карта"][0], "bad")
                self.assertEqual(r["Привязка к оператору"][0], "bad")

    def test_pin_and_puk(self):
        self.assertEqual(sim(SIMStatus="kCTSIMSupportSIMStatusPINLocked")["SIM-карта"][0], "warn")
        self.assertEqual(sim(SIMStatus="kCTSIMSupportSIMStatusPUKLocked")["SIM-карта"][0], "bad")

    def test_unknown_status_is_shown_as_is(self):
        r = sim(SIMStatus="kCTSIMSupportSIMStatusSomethingNew")
        self.assertEqual(r["SIM-карта"], ("info", "Состояние: SomethingNew"))

    def test_wifi_only_ipad_has_no_sim_check(self):
        self.assertEqual(core.sim_checks({"TelephonyCapability": False}), [])

    def test_every_message_is_translated(self):
        tree = ast.parse((ROOT / "iactivator" / "core.py").read_text(encoding="utf-8"))
        fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "sim_checks")
        texts = {n.value for n in ast.walk(fn) if isinstance(n, ast.Constant) and isinstance(n.value, str)
                 and any("Ѐ" <= ch <= "ӿ" for ch in n.value)}
        missing = sorted(x for x in texts if x not in i18n.EN or x not in i18n.UK)
        self.assertEqual(missing, [])

    def test_english(self):
        i18n.set_lang("en")
        r = {c["name"]: c["detail"] for c in core.sim_checks(PHONE)}
        self.assertIn("Working · Kyivstar · ICCID …1234", r["SIM card"])


if __name__ == "__main__":
    unittest.main()
