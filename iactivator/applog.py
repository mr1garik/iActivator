"""Program journal: what happened, when, with which device.

Entries are kept in memory for the Journal page and appended to a daily text file
(logs/YYYY-MM-DD.log in the app data folder), so a problem can be looked at later.
Error details (tracebacks) go in as "debug" entries, shown only in the detailed view.
"""
from __future__ import annotations

import threading
import traceback
from datetime import datetime, timedelta

from .core import app_data_dir
from .i18n import t

KEEP_DAYS = 30
LEVELS = {"debug": "DEBUG", "info": "INFO ", "ok": "OK   ", "warn": "WARN ", "error": "ERROR"}

_lock = threading.Lock()
_entries: list[dict] = []
_dropped = 0         # entries trimmed from memory; positions handed to the window stay valid
MAX_IN_MEMORY = 5000  # older entries stay in the daily files
KEEP_AFTER_TRIM = 4000


def logs_dir():
    d = app_data_dir() / "logs"
    d.mkdir(exist_ok=True)
    return d


def _guess_level(text: str) -> str:
    if text.startswith(("❌", "⛔")):
        return "error"
    if text.startswith("⚠") or text.lstrip().startswith("⚠"):
        return "warn"
    if text.startswith("✅"):
        return "ok"
    return "info"


def add(text: str, serial: str = "", level: str = "") -> None:
    global _dropped
    text = t(text)
    now = datetime.now()
    e = {"time": now.strftime("%H:%M:%S"), "level": level or _guess_level(text), "serial": serial or "", "text": text}
    with _lock:
        _entries.append(e)
        if len(_entries) > MAX_IN_MEMORY:
            cut = len(_entries) - KEEP_AFTER_TRIM
            del _entries[:cut]
            _dropped += cut
        try:
            with open(logs_dir() / f"{now:%Y-%m-%d}.log", "a", encoding="utf-8") as f:
                f.write(f"{now:%Y-%m-%d %H:%M:%S} {LEVELS[e['level']]} {e['serial'] or '-':<14} {text}\n")
        except OSError:
            pass


def exception(e: BaseException, serial: str = "") -> None:
    """Full traceback for the detailed view and the log file."""
    add("".join(traceback.format_exception(type(e), e, e.__traceback__)).rstrip(), serial, "debug")


def since(n: int) -> tuple[list[dict], int]:
    """Entries after position n (as returned by a previous call) and the new position."""
    with _lock:
        return _entries[max(n - _dropped, 0):], _dropped + len(_entries)


def cleanup() -> None:
    """Delete daily files older than KEEP_DAYS."""
    cutoff = f"{datetime.now() - timedelta(days=KEEP_DAYS):%Y-%m-%d}"
    for p in logs_dir().glob("*.log"):
        if p.stem < cutoff:
            try:
                p.unlink()
            except OSError:
                pass
