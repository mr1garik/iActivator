"""Start iActivator together with Windows, per-user and without admin rights.

Uses the HKCU \\...\\Run registry key. A no-op on other systems, so the rest of the
program can call it unconditionally.
"""
from __future__ import annotations

import os
import sys

_NAME = "iActivator"
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def supported() -> bool:
    return sys.platform == "win32"


def _command() -> str:
    if getattr(sys, "frozen", False):  # packaged .exe: the executable starts the app itself
        return f'"{sys.executable}"'
    main = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
    return f'"{sys.executable}" "{main}"'  # running from source (python main.py)


def is_enabled() -> bool:
    if not supported():
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, _NAME)
            return bool(value)
    except OSError:
        return False


def _recorded_program(value: str) -> str:
    """The program path in a Run entry: '"C:\\…\\iActivator.exe" args' or an unquoted path."""
    value = value.strip()
    if value.startswith('"'):
        return value[1:].split('"', 1)[0]
    return value.split(" ", 1)[0]


def repair() -> bool:
    """If start-up with Windows is on but points to a program that no longer exists (an old
    portable iActivator.exe that was deleted or moved after installing), point it here.
    Another copy that still exists is left alone. Returns True when the entry was changed."""
    if not supported():
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, _NAME)
    except OSError:
        return False
    if not value or os.path.exists(_recorded_program(str(value))):
        return False
    set_enabled(True)
    return True


def set_enabled(on: bool) -> bool:
    """Add or remove the startup entry; returns the resulting state."""
    if not supported():
        return False
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
        if on:
            winreg.SetValueEx(key, _NAME, 0, winreg.REG_SZ, _command())
        else:
            try:
                winreg.DeleteValue(key, _NAME)
            except OSError:
                pass
    return is_enabled()
