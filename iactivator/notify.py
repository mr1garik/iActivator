"""A sound and a system notification when a phone is done, so the user can do something
else while the queue runs. Never raises: a missing notification must not affect a job."""
from __future__ import annotations

import subprocess
import sys
import threading

from . import settings


def enabled() -> bool:
    try:
        return bool(settings.load()["ui"].get("notify", True))
    except Exception:
        return False


def _applescript_text(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def mac_command(title: str, message: str, ok: bool) -> list[str]:
    sound = "Glass" if ok else "Basso"
    script = (f"display notification {_applescript_text(message)} with title {_applescript_text(title)} "
              f"sound name {_applescript_text(sound)}")
    return ["osascript", "-e", script]


def _show(title: str, message: str, ok: bool) -> None:
    try:
        if sys.platform == "darwin":
            subprocess.run(mac_command(title, message, ok), timeout=10, capture_output=True)
        elif sys.platform == "win32":
            import winsound
            winsound.MessageBeep(winsound.MB_OK if ok else winsound.MB_ICONHAND)
            from . import tray
            if tray._icon is not None:  # the tray icon shows the balloon / toast
                tray._icon.notify(message, title)
    except Exception:
        pass


def phone_done(label: str, action: str, ok: bool, detail: str = "") -> None:
    """Called when a job on one phone finishes (in the background, so it never delays it)."""
    if not enabled():
        return
    from .i18n import t
    title = ("✅ " if ok else "❌ ") + (t("{action}: готово", action=t(action)) if ok
                                       else t("{action}: ошибка", action=t(action)))
    message = label + (f" — {detail}" if detail else "")
    threading.Thread(target=_show, args=(title, message[:200], ok), daemon=True).start()
