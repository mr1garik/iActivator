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
sys.modules.setdefault("keyring", MagicMock())
sys.modules.setdefault("pymobiledevice3.services.mobile_image_mounter", MagicMock())

from unittest import mock  # noqa: E402
from iactivator import webui  # noqa: E402


class OpenUrl(unittest.TestCase):
    def test_macos_uses_open(self):
        with mock.patch.object(webui.sys, "platform", "darwin"), \
             mock.patch.object(webui.subprocess, "Popen") as popen:
            self.assertTrue(webui.open_url("https://github.com/mr1garik/iActivator"))
        popen.assert_called_once_with(["open", "https://github.com/mr1garik/iActivator"])

    def test_linux_uses_xdg_open(self):
        with mock.patch.object(webui.sys, "platform", "linux"), \
             mock.patch.object(webui.subprocess, "Popen") as popen:
            webui.open_url("https://x")
        popen.assert_called_once_with(["xdg-open", "https://x"])

    def test_falls_back_to_webbrowser_when_the_opener_fails(self):
        with mock.patch.object(webui.sys, "platform", "darwin"), \
             mock.patch.object(webui.subprocess, "Popen", side_effect=OSError), \
             mock.patch.object(webui.webbrowser, "open", return_value=True) as wb:
            self.assertTrue(webui.open_url("https://x"))
        wb.assert_called_once_with("https://x")


if __name__ == "__main__":
    unittest.main()
