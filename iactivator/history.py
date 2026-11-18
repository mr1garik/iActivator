"""History of processed devices: who was connected and what was done with them.

Kept in history.json (app data folder), which is read once and then kept in memory:
every change is written to the file right away, but nothing is re-read or re-parsed.
history.csv next to it (for Excel) is rebuilt a few seconds after the last change and
before it is opened, not on every event, so a long history does not slow each step down.
"""
from __future__ import annotations

import atexit
import copy
import csv
import json
import threading
from datetime import datetime

from .core import app_data_dir
from .i18n import t as tr

_lock = threading.RLock()
_cache: dict | None = None   # the history, as in history.json
_csv_timer: threading.Timer | None = None
CSV_DELAY = 3.0  # seconds after the last change
RESULT = {"ok": "Успешно", "warn": "Замечания", "error": "Ошибка", "info": ""}


def json_path():
    return app_data_dir() / "history.json"


def csv_path():
    return app_data_dir() / "history.csv"


def _load() -> dict:
    """The history (call with _lock held). Read from disk only the first time."""
    global _cache
    if _cache is None:
        try:
            _cache = _migrate(json.loads(json_path().read_text(encoding="utf-8")))
        except (OSError, ValueError):
            _cache = {}
        from .models import model_name
        for d in _cache.values():  # names added in a later version replace stored identifiers
            if isinstance(d, dict) and d.get("model"):
                d["model_name"] = model_name(d["model"])
        try:
            if _cache and (not csv_path().exists() or csv_path().stat().st_mtime < json_path().stat().st_mtime):
                _schedule_csv()  # the table is missing or older than the history
        except OSError:
            pass
    return _cache


def _reset_cache() -> None:
    """Forget the in-memory copy (tests, or after the file was replaced)."""
    global _cache
    with _lock:
        _cache = None


def _is_udid(s: str) -> bool:
    """A connection identifier (UDID/ECID), not a human serial number like 'L4VKQY7W10'."""
    return bool(s) and (len(s) >= 20 or "-" in s or "~" in s)


def _window(d: dict) -> tuple[str, str]:
    times = [e["time"] for e in d.get("events", []) if e.get("time")]
    times += [t for t in (d.get("first_seen"), d.get("last_seen")) if t]
    return (min(times), max(times)) if times else ("", "")


def _migrate(data: dict) -> dict:
    """Older versions stored one physical phone under two keys — its connection id
    (holding the events) and its serial number (holding the model, IMEI, iOS). Give
    every record an explicit id and glue such split pairs back into one row."""
    for key, d in data.items():
        d.setdefault("id", key)
    # info-only record (serial key, has model, no events) -> merge into the overlapping
    # events-only record (connection-id key, has events, no model).
    info_only = [d for d in data.values()
                 if (d.get("model_name") or d.get("model")) and not d.get("events") and not _is_udid(d["id"])]
    event_only = [d for d in data.values()
                  if d.get("events") and not (d.get("model_name") or d.get("model")) and _is_udid(d["id"])]
    drop = []
    for b in info_only:
        bs, be = _window(b)
        hits = [a for a in event_only if (aw := _window(a)) and aw[0] <= be and bs <= aw[1]]
        if len(hits) != 1:
            continue  # ambiguous: leave both records untouched
        a = hits[0]
        a["serial"] = b.get("serial") or b["id"]  # show the human serial number
        for k, v in b.items():
            if k not in ("id", "serial", "events") and v and not a.get(k):
                a[k] = v
        drop.append(b["id"])
        event_only.remove(a)
    for key in drop:
        data.pop(key, None)
    return data


def _save(data: dict) -> None:
    tmp = json_path().with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(json_path())
    _schedule_csv()


def _schedule_csv() -> None:
    global _csv_timer
    with _lock:
        if _csv_timer is None:
            _csv_timer = threading.Timer(CSV_DELAY, flush_csv)
            _csv_timer.daemon = True
            _csv_timer.start()


def flush_csv() -> None:
    """Write history.csv now (before it is opened, and on exit)."""
    global _csv_timer
    with _lock:
        if _csv_timer is not None:
            _csv_timer.cancel()
            _csv_timer = None
        _write_csv(_load())


atexit.register(flush_csv)


def _write_csv(data: dict) -> None:
    # One row per event; ";" and a BOM so Excel with a Russian locale opens it correctly.
    try:
        with open(csv_path(), "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow([tr(h) for h in ("Дата и время", "Серийный №", "IMEI", "IMEI 2", "Модель", "Память", "iOS", "Действие", "Результат", "Подробности", "Заметка")])
            rows = [(e, d) for d in data.values() for e in d.get("events", [])]
            for e, d in sorted(rows, key=lambda r: r[0]["time"]):
                w.writerow([e["time"], d.get("serial") or d.get("id") or "", d.get("imei") or "", d.get("imei2") or "", tr(d.get("model_name") or d.get("model") or ""),
                            d.get("capacity") or "", d.get("ios") or "", tr(e["action"]), tr(RESULT.get(e["result"], e["result"])), e.get("detail", ""), d.get("note", "")])
    except OSError:
        pass  # the file is open in Excel; it will be rewritten on the next change


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _entry(data: dict, device_id: str) -> dict:
    # Keyed by the connection id (UDID) so events and device facts land in one row;
    # "serial" holds the human serial number for display and stays empty until it is read.
    return data.setdefault(device_id, {"id": device_id, "serial": "", "first_seen": _now(), "events": []})


MAX_BATTERY_LOG = 60  # points kept per device (one per day); enough to see a trend


def _record_battery(d: dict, health, cycles) -> None:
    """Keep how the battery changed over time: one point per day (the latest that day),
    and a new point only when health or cycles differ, so a replaced battery stands out."""
    try:
        entry = {"t": datetime.now().strftime("%Y-%m-%d"), "h": int(health),
                 "c": int(cycles) if cycles is not None else None}
    except (TypeError, ValueError):
        return
    log = d.setdefault("battery_log", [])
    if log and log[-1]["t"] == entry["t"]:
        log[-1] = entry
    elif not log or log[-1]["h"] != entry["h"] or log[-1]["c"] != entry["c"]:
        log.append(entry)
    del log[:-MAX_BATTERY_LOG]


def update_device(info: dict) -> None:
    """Store the latest known facts about a device (model, IMEI, battery…)."""
    device_id = info.get("conn_id") or info.get("serial")
    if not device_id:
        return
    with _lock:
        data = _load()
        d = _entry(data, device_id)
        if info.get("serial"):
            d["serial"] = info["serial"]
        for k in ("imei", "imei2", "model", "model_name", "capacity", "ios", "name"):
            if info.get(k):
                d[k] = info[k]
        b = info.get("battery") or {}
        if b.get("health") is not None:
            d["battery"] = b["health"]
            _record_battery(d, b.get("health"), b.get("cycles"))
        d["activation"] = info.get("activation") or d.get("activation")
        d["last_seen"] = _now()
        _save(data)


def add_event(serial: str, action: str, result: str, detail: str = "") -> None:
    """result: ok | warn | error | info."""
    if not serial:
        return
    with _lock:
        data = _load()
        d = _entry(data, serial)
        d["events"].append({"time": _now(), "action": action, "result": result, "detail": detail})
        d["last_seen"] = _now()
        _save(data)


def parts_baseline(device_id: str) -> tuple:
    """Part serial numbers recorded the first time this iPhone was checked, and when."""
    with _lock:
        p = (_load().get(device_id) or {}).get("parts")
        return (dict(p["serials"]), p.get("time")) if p and p.get("serials") else (None, None)


def record_parts(device_id: str, serials: dict) -> None:
    """The first record becomes the reference. Later checks only add parts that were not
    readable before; a recorded serial number is never overwritten, so a replaced part keeps
    being reported."""
    if not device_id or not serials:
        return
    with _lock:
        data = _load()
        d = _entry(data, device_id)
        p = d.get("parts")
        if not p or not p.get("serials"):
            d["parts"] = {"time": _now(), "serials": dict(serials)}
        else:
            for k, v in serials.items():
                p["serials"].setdefault(k, v)
        _save(data)


def summary() -> dict:
    with _lock:
        # A copy, because the window serialises it after the lock is released. Event entries
        # are never changed once added, so copying each device and its event list is enough.
        data = {k: {**d, "events": list(d.get("events", []))} for k, d in _load().items()}
    today = datetime.now().strftime("%Y-%m-%d")
    devices = sorted(data.values(), key=lambda d: d.get("last_seen", ""), reverse=True)
    def did(d, action, result="ok"):
        return any(e["action"] == action and e["result"] == result for e in d.get("events", []))
    return {
        "devices": devices,
        "stats": {
            "total": len(devices),
            "today": sum(1 for d in devices if d.get("last_seen", "").startswith(today)),
            "activated": sum(1 for d in devices if did(d, "Активация")),
            "faulty": sum(1 for d in devices if did(d, "Диагностика", "error") or did(d, "Локатор и MDM", "error")),
        },
        "csv": str(csv_path()),
    }


def stats_report(days: int = 30) -> dict:
    """Totals and a per-day series for the Statistics view: activations (Активация, ok) and
    diagnostics runs (Диагностика), for today / the last 7 and 30 days / all time."""
    from datetime import timedelta
    today = datetime.now().date()
    start = today - timedelta(days=days - 1)
    week = today - timedelta(days=6)
    month = today - timedelta(days=29)
    series = {(start + timedelta(i)).isoformat(): {"act": 0, "check": 0} for i in range(days)}
    tot = {"act": {"today": 0, "week": 0, "month": 0, "all": 0},
           "check": {"today": 0, "week": 0, "month": 0, "all": 0}}
    with _lock:
        data = {k: list(d.get("events", [])) for k, d in _load().items()}
    for events in data.values():
        for e in events:
            if e.get("action") == "Активация" and e.get("result") == "ok":
                kind = "act"
            elif e.get("action") == "Диагностика":
                kind = "check"
            else:
                continue
            day = (e.get("time") or "")[:10]
            tot[kind]["all"] += 1
            if day:
                if day == today.isoformat():
                    tot[kind]["today"] += 1
                if day >= week.isoformat():
                    tot[kind]["week"] += 1
                if day >= month.isoformat():
                    tot[kind]["month"] += 1
                if day in series:
                    series[day][kind] += 1
    return {"totals": tot, "days": [{"d": d, **v} for d, v in sorted(series.items())]}


NOTE_MAX = 1000


def set_note(device_id: str, text: str) -> bool:
    """The user's own note for a phone (price, customer, defects). Empty text removes it."""
    text = (text or "").strip()[:NOTE_MAX]
    with _lock:
        data = _load()
        d = data.get(device_id)
        if d is None:
            return False
        if text:
            d["note"] = text
        else:
            d.pop("note", None)
        _save(data)
    return True


def note(device_id: str) -> str:
    with _lock:
        return (_load().get(device_id) or {}).get("note", "")


def delete(serial: str) -> None:
    with _lock:
        data = _load()
        data.pop(serial, None)
        _save(data)


def clear() -> int:
    """Forget every device: empty history.json and delete history.csv. Returns how many
    devices there were."""
    global _csv_timer
    with _lock:
        data = _load()
        n = len(data)
        data.clear()
        _save(data)
        if _csv_timer is not None:
            _csv_timer.cancel()
            _csv_timer = None
        try:
            csv_path().unlink()
        except OSError:
            pass  # not made yet, or open in Excel (it is rewritten empty on the next change)
    return n


def remove_older(cutoff: str) -> int:
    """Forget devices last seen before cutoff ("YYYY-MM-DD HH:MM:SS"). Returns how many."""
    with _lock:
        data = _load()
        old = [k for k, d in data.items() if (d.get("last_seen") or d.get("first_seen") or "") < cutoff]
        for k in old:
            del data[k]
        if old:
            _save(data)
    return len(old)


def export() -> dict:
    with _lock:
        return copy.deepcopy(_load())


def merge(other: dict) -> int:
    """Add devices and events from another computer's history; returns how many devices it had."""
    with _lock:
        data = _load()
        for serial, d in other.items():
            if not isinstance(d, dict) or not d.get("events") and not d.get("model"):
                continue
            mine = data.setdefault(serial, {k: v for k, v in d.items() if k != "events"} | {"events": []})
            seen = {(e["time"], e["action"]) for e in mine["events"]}
            mine["events"] += [e for e in d.get("events", []) if (e.get("time"), e.get("action")) not in seen]
            mine["events"].sort(key=lambda e: e["time"])
            for k, v in d.items():
                if k != "events" and v and not mine.get(k):
                    mine[k] = v
            if d.get("last_seen", "") > mine.get("last_seen", ""):
                mine["last_seen"] = d["last_seen"]
        _save(data)
    return len(other)
