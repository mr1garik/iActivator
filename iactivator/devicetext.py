"""One small text file per iPhone, made from the history: the device's facts, the part
serial numbers recorded at the first check, and every event. A few kilobytes each,
readable anywhere (Notepad, TextEdit, a phone).

clear_all() deletes these files, the PDF reports and the device history in one go.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from . import history
from .core import PART_KEYS, app_data_dir
from .i18n import t

FOLDER = "TXT"
RESULT_MARK = {"ok": "✓", "warn": "!", "error": "✗", "info": "·"}


def texts_dir(create: bool = True) -> Path:
    d = app_data_dir() / FOLDER
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d


def _capacity(text):
    m = re.fullmatch(r"\s*(\d+)\s*(ГБ|ТБ|GB|TB)\s*", str(text or ""))
    return t("{n} ТБ" if m.group(2) in ("ТБ", "TB") else "{n} ГБ", n=m.group(1)) if m else (text or "")


def _activation(state):
    if not state:
        return ""
    return t("не активирован") if state == "Unactivated" else t("активирован") if state == "Activated" else state


def render(d: dict) -> str:
    """The text for one device from its history entry."""
    model = t(d.get("model_name") or "") or d.get("model") or "iPhone"
    title = model + (f", {_capacity(d['capacity'])}" if d.get("capacity") else "")
    rows = [
        (t("Серийный №"), d.get("serial")),
        ("IMEI", d.get("imei")),
        ("IMEI 2", d.get("imei2")),
        (t("Модель"), d.get("model")),
        ("iOS", d.get("ios")),
        (t("Батарея (здоровье)"), (f"{min(d['battery'], 100)}%" + (f" ({t('новая батарея')})" if d["battery"] > 100 else ""))
                                       if isinstance(d.get("battery"), (int, float)) else ""),
        (t("Активация"), _activation(d.get("activation"))),
        (t("Имя"), d.get("name")),
        (t("Впервые подключён"), d.get("first_seen")),
        (t("Последний раз"), d.get("last_seen")),
        ("UDID", d.get("id") if d.get("id") != d.get("serial") else ""),
    ]
    width = max(len(k) for k, v in rows if v) if any(v for _, v in rows) else 0
    out = [title, "=" * len(title), ""]
    out += [f"{k + ':':<{width + 1}} {v}" for k, v in rows if v]
    if d.get("note"):
        out += ["", t("Заметка") + ":", d["note"]]

    parts = (d.get("parts") or {}).get("serials") or {}
    if parts:
        out += ["", t("Серийные номера деталей (записаны {time})", time=d["parts"].get("time", "")),
                "-" * 40]
        names = {k: t(v) for k, v in PART_KEYS.items()}
        pw = max(len(names.get(k, k)) for k in parts)
        out += [f"{names.get(k, k) + ':':<{pw + 1}} {v}" for k, v in parts.items()]

    events = d.get("events") or []
    out += ["", t("События ({n})", n=len(events)), "-" * 40]
    for e in events:
        line = f"{e.get('time', '')}  {RESULT_MARK.get(e.get('result'), '·')} {t(e.get('action', ''))}"
        if e.get("detail"):
            line += f": {t(e['detail'])}"
        out.append(line)
    if not events:
        out.append(t("Событий нет"))
    out += ["", t("Создано в iActivator {time}", time=datetime.now().strftime("%Y-%m-%d %H:%M"))]
    return "\n".join(out) + "\n"


def _file_name(d: dict) -> str:
    model = t(d.get("model_name") or "") or d.get("model") or "iPhone"
    ident = d.get("serial") or (d.get("id") or "")[:12]
    name = f"{model} {ident}".strip()
    name = re.sub(r'[\\/:*?"<>|\r\n\t]+', " ", name)   # not allowed in Windows file names
    return re.sub(r"\s+", " ", name).strip()[:80] + ".txt"


def save(device_ids: list[str] | None = None) -> list[Path]:
    """Write (or overwrite) one file per device; all devices when no ids are given.
    The file is named after the model and serial number, so saving again updates it
    instead of adding another copy."""
    data = history.export()
    ids = list(data) if device_ids is None else [i for i in device_ids if i in data]
    folder = texts_dir()
    paths = []
    for i in ids:
        p = folder / _file_name(data[i])
        # Windows Notepad needs the BOM to read Cyrillic correctly in old versions.
        p.write_text(render(data[i]), encoding="utf-8-sig", newline="\r\n" if _windows() else "\n")
        paths.append(p)
    return paths


def _windows() -> bool:
    import sys
    return sys.platform == "win32"


def _folders() -> list[Path]:
    # The PDF reports folder (report.reports_dir), named here so this module does not load the PDF library.
    # The same for the stickers folder (labels.FOLDER).
    return [texts_dir(create=False), app_data_dir() / "Отчёты", app_data_dir() / "Наклейки"]


def usage() -> dict:
    """How many TXT and PDF files there are and how much space they take."""
    files = size = 0
    for folder in _folders():
        if folder.is_dir():
            for p in folder.iterdir():
                if p.is_file() and p.suffix.lower() in (".txt", ".pdf"):
                    files += 1
                    size += p.stat().st_size
    return {"files": files, "bytes": size}


def clear_files() -> dict:
    """Delete the TXT files and PDF reports (only those, nothing else in the folders).
    The history stays, so any file can be made again."""
    removed = freed = 0
    for folder in _folders():
        if not folder.is_dir():
            continue
        for p in folder.iterdir():
            if p.is_file() and p.suffix.lower() in (".txt", ".pdf"):
                try:
                    size = p.stat().st_size
                    p.unlink()
                    removed += 1
                    freed += size
                except OSError:
                    pass  # open in another program: left for next time
    return {"removed": removed, "bytes": freed}


def cleanup(days: int, now: datetime | None = None) -> dict:
    """Automatic cleanup: forget phones not seen for `days` days and delete TXT/PDF files
    older than that. Does nothing when days is 0."""
    if not days:
        return {"removed": 0, "bytes": 0, "devices": 0}
    from datetime import timedelta
    now = now or datetime.now()
    cutoff = now - timedelta(days=days)
    removed = freed = 0
    for folder in _folders():
        if not folder.is_dir():
            continue
        for p in folder.iterdir():
            try:
                if p.is_file() and p.suffix.lower() in (".txt", ".pdf") and \
                        datetime.fromtimestamp(p.stat().st_mtime) < cutoff:
                    size = p.stat().st_size
                    p.unlink()
                    removed += 1
                    freed += size
            except OSError:
                pass
    devices = history.remove_older(cutoff.strftime("%Y-%m-%d %H:%M:%S"))
    return {"removed": removed, "bytes": freed, "devices": devices}


def clear_all() -> dict:
    """Delete the TXT files, the PDF reports and the device history."""
    r = clear_files()
    r["devices"] = history.clear()
    return r
