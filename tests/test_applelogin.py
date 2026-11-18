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


import asyncio  # noqa: E402
from unittest import mock  # noqa: E402

from iactivator import core  # noqa: E402

FORM1 = b"""<xmlui>
 <page><navigationBar title="Activation Lock"/>
  <tableView><section>
   <editableTextRow id="appleId" label="Apple ID" placeholder="you@icloud.com"/>
   <editableTextRow id="password" label="Password" secure="true"/>
   <footer>Sign in with the Apple ID that was used to set up this iPhone.</footer>
  </section></tableView></page>
 <serverInfo sessionId="S1" iosVersion="27.0"/>
</xmlui>"""

FORM2 = b"""<xmlui>
 <page><navigationBar title="Two-Factor"/>
  <tableView><section>
   <editableTextRow id="code" label="Verification Code"/>
   <footer>Enter the code shown on a trusted device.</footer>
  </section></tableView></page>
 <serverInfo sessionId="S2"/>
</xmlui>"""


class ParseForm(unittest.TestCase):
    def test_fields_server_info_and_secure(self):
        f = core.parse_activation_form(FORM1)
        self.assertEqual(f["title"], "Activation Lock")
        self.assertIn("set up this iPhone", f["description"])
        self.assertEqual([x["id"] for x in f["fields"]], ["appleId", "password"])
        self.assertFalse(f["fields"][0]["secure"])
        self.assertTrue(f["fields"][1]["secure"])  # password masked
        self.assertEqual(f["fields"][0]["placeholder"], "you@icloud.com")
        self.assertEqual(f["server_info"], {"sessionId": "S1", "iosVersion": "27.0"})

    def test_code_field_is_treated_as_secret_by_label(self):
        self.assertTrue(core.parse_activation_form(FORM2)["fields"][0]["secure"])


class FakeService:
    """Stands in for Apple + the device: returns the forms, then an activation record."""
    def __init__(self, lockdown):
        self.lockdown = lockdown
        self.posts = []        # (url, data) for every POST to Apple
        self.applied = False
        self._seq = [(FORM1, {"Content-Type": "application/x-buddyml"}),
                     (FORM2, {"Content-Type": "application/x-buddyml"}),
                     (b"<record/>", {"Content-Type": "text/xml"})]

    async def state(self):
        return "Unactivated"

    async def create_activation_session_info(self):
        return {"blob": 1}

    async def create_activation_info_with_session(self, handshake):
        return {"info": 1}

    def post(self, url, data, headers=None):
        self.posts.append((url, dict(data) if isinstance(data, dict) else "bytes"))  # copy: submit() clears the original
        if isinstance(data, dict) and "activation-info" not in data:
            return self._seq.pop(0)          # a form answer
        if isinstance(data, dict):
            return self._seq.pop(0)          # the initial activation-info POST
        return (b"handshake", {})            # the DRM handshake POST (bytes body)

    async def activate_with_session(self, content, headers):
        self.applied = True

    async def activate_with_lockdown(self, content):
        self.applied = True


class FakeLockdown:
    def __init__(self):
        self.acknowledged = False
    async def get_value(self, key=None):
        return {"ActivationInfo": 1}
    async def set_value(self, value, key=None):
        if key == "ActivationStateAcknowledged":
            self.acknowledged = True
    async def close(self):
        pass


class Flow(unittest.TestCase):
    def setUp(self):
        self.lock = FakeLockdown()
        self.svc = FakeService(self.lock)
        async def fake_usbmux(*a, **k):
            return self.lock
        self.p1 = mock.patch.object(core, "create_using_usbmux", fake_usbmux)
        self.p2 = mock.patch.object(core, "MobileActivationService", lambda ld: self.svc)
        self.p1.start(); self.p2.start()
        self.addCleanup(self.p1.stop); self.addCleanup(self.p2.stop)

    def test_two_step_signin_sends_credentials_only_to_apple_and_activates(self):
        a = core.AppleIDActivation("SER1", lambda m: None)
        r1 = asyncio.run(a.start())
        self.assertEqual([f["id"] for f in r1["form"]["fields"]], ["appleId", "password"])

        r2 = asyncio.run(a.submit({"appleId": "me@icloud.com", "password": "secret"}))
        self.assertEqual(r2["form"]["title"], "Two-Factor")  # 2FA step next
        # The password went to Apple with the form's hidden server_info merged in.
        last = self.svc.posts[-1][1]
        self.assertEqual(last["password"], "secret")
        self.assertEqual(last["sessionId"], "S1")

        r3 = asyncio.run(a.submit({"code": "123456"}))
        self.assertEqual(r3, {"activated": True})
        self.assertTrue(self.svc.applied)
        self.assertTrue(self.lock.acknowledged)
        asyncio.run(a.close())
        self.assertIsNone(a.lockdown)
        self.assertEqual(a._server_info, {})  # nothing kept after closing

    def test_already_activated_phone_needs_no_signin(self):
        self.svc.state = lambda: _done("Activated")
        a = core.AppleIDActivation("SER1", lambda m: None)
        self.assertEqual(asyncio.run(a.start()), {"activated": True})

    def test_submit_without_start_is_refused(self):
        a = core.AppleIDActivation("SER1", lambda m: None)
        with self.assertRaises(core.UserFacingError):
            asyncio.run(a.submit({"x": "y"}))


async def _done(v):
    return v


if __name__ == "__main__":
    unittest.main()
