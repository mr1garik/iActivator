"""Stickers with a QR code for checked phones (an option, turned on in Settings).

Each sticker is a PDF page of exactly the label's size, so it prints on any printer
(a label printer or an A4 sheet of stickers) without a driver for that printer.
The QR code is drawn as vector squares: sharp at any size, no image library needed.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import segno
from fpdf import FPDF

from . import history
from .core import app_data_dir
from .i18n import t
from .report import FONTS, open_file

FOLDER = "Наклейки"

# Label sizes in mm (width, height). "a4" is a sheet of 3 × 8 stickers of 70 × 37 mm.
SIZES = {"40x30": (40, 30), "50x30": (50, 30), "58x40": (58, 40), "62x29": (62, 29), "a4": (70, 37)}
A4_GRID = (3, 8)
QR_MODES = ("text", "serial")
# Lines the user can turn on or off (the note is "note", kept from the first version).
LINES = ("model", "serial", "imei", "battery", "verdict", "date", "note")
DEFAULT_LINES = {"model": True, "serial": True, "imei": True, "battery": True, "verdict": True, "date": True}
FIELD_MAX, FOOTER_MAX = 20, 40
DEFAULTS = {"enabled": False, "size": "40x30", "qr": "text", "note": False,
            "show": dict(DEFAULT_LINES), "field": "", "footer": ""}


def _clean(text, limit: int) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()[:limit]


def options(ui: dict) -> dict:
    """The sticker settings with defaults for anything missing or not allowed."""
    o = {**DEFAULTS, "show": dict(DEFAULT_LINES)}
    saved = ui.get("labels") if isinstance(ui.get("labels"), dict) else {}
    if isinstance(saved.get("enabled"), bool):
        o["enabled"] = saved["enabled"]
    if saved.get("size") in SIZES:
        o["size"] = saved["size"]
    if saved.get("qr") in QR_MODES:
        o["qr"] = saved["qr"]
    if isinstance(saved.get("note"), bool):
        o["note"] = saved["note"]
    if isinstance(saved.get("show"), dict):
        for k, v in saved["show"].items():
            if k in DEFAULT_LINES and isinstance(v, bool):
                o["show"][k] = v
    o["field"] = _clean(saved.get("field"), FIELD_MAX)
    o["footer"] = _clean(saved.get("footer"), FOOTER_MAX)
    return o


def labels_dir() -> Path:
    d = app_data_dir() / FOLDER
    d.mkdir(parents=True, exist_ok=True)
    return d


def _capacity(text) -> str:
    m = re.fullmatch(r"\s*(\d+)\s*(ГБ|ТБ|GB|TB)\s*", str(text or ""))
    return t("{n} ТБ" if m.group(2) in ("ТБ", "TB") else "{n} ГБ", n=m.group(1)) if m else str(text or "")


def verdict(d: dict) -> str:
    """The result of the latest diagnostics, as in the PDF report; empty if never checked."""
    for e in reversed(d.get("events") or []):
        if e.get("action") == "Диагностика":
            return {"ok": t("Годен"), "warn": t("Годен с замечаниями"), "error": t("Не годен")}.get(e.get("result"), "")
    return ""


def lines_for(d: dict, opts) -> list[tuple[str, bool]]:
    """What is printed next to the QR code: (text, bold), in the order and with the lines
    chosen in Settings. opts may also be a bool (old call: only whether to add the note)."""
    if isinstance(opts, bool):
        opts = {**DEFAULTS, "note": opts}
    show = {**DEFAULT_LINES, **(opts.get("show") or {})}
    out = []
    if show["model"]:
        model = t(d.get("model_name") or "") or d.get("model") or "iPhone"
        out.append((model + (f" · {_capacity(d['capacity'])}" if d.get("capacity") else ""), True))
    if show["serial"] and d.get("serial"):
        out.append((f"S/N {d['serial']}", False))
    if show["imei"] and d.get("imei"):
        out.append((f"IMEI {d['imei']}", False))
    if show["battery"]:
        extra = []
        if isinstance(d.get("battery"), (int, float)):
            extra.append(f"{t('Батарея')} {min(int(d['battery']), 100)}%")
        if d.get("ios"):
            extra.append(f"iOS {d['ios']}")
        if extra:
            out.append((" · ".join(extra), False))
    v = verdict(d) if show["verdict"] else ""
    date = (d.get("last_seen") or "")[:10] if show["date"] else ""
    if v or date:
        out.append((" · ".join(x for x in (v, date) if x), bool(v)))
    if opts.get("note") and d.get("note"):
        note = d["note"].replace("\n", " ")
        field = opts.get("field")
        out.append((f"{field}: {note}" if field else note, bool(field)))
    if opts.get("footer"):
        out.append((opts["footer"], False))
    return out or [(d.get("serial") or "iPhone", False)]


def qr_text(d: dict, mode: str) -> str:
    """serial: just the serial number (a scanner finds the phone by it); text: the facts
    in plain text that any phone camera shows."""
    if mode == "serial":
        return d.get("serial") or d.get("id") or ""
    model = t(d.get("model_name") or "") or d.get("model") or "iPhone"
    parts = [model + (f" {_capacity(d['capacity'])}" if d.get("capacity") else "")]
    for label, key in (("S/N", "serial"), ("IMEI", "imei"), ("IMEI2", "imei2"), ("iOS", "ios")):
        if d.get(key):
            parts.append(f"{label}: {d[key]}")
    if isinstance(d.get("battery"), (int, float)):
        parts.append(f"{t('Батарея')}: {min(int(d['battery']), 100)}%")
    v = verdict(d)
    if v:
        parts.append(v)
    return "\n".join(parts)


class _Labels(FPDF):
    def __init__(self, size: str):
        w, h = SIZES["a4"] if size == "a4one" else SIZES[size]
        super().__init__(unit="mm", format=(210, 297) if size == "a4" else (w, h))
        for regular, bold in FONTS:
            if Path(regular).exists() and Path(bold).exists():
                self.add_font("ui", "", regular)
                self.add_font("ui", "B", bold)
                break
        else:
            raise RuntimeError(t("Не найден шрифт с кириллицей для PDF"))
        self.set_auto_page_break(False)
        self.set_margins(0, 0, 0)


def _draw_qr(pdf: FPDF, data: str, x: float, y: float, side: float) -> None:
    qr = segno.make(data or "-", error="m", micro=False)
    rows = list(qr.matrix)
    n = len(rows)
    cell = side / n
    pdf.set_fill_color(0, 0, 0)
    for r, row in enumerate(rows):
        c = 0
        while c < n:
            if row[c]:
                start = c
                while c < n and row[c]:
                    c += 1
                pdf.rect(x + start * cell, y + r * cell, (c - start) * cell, cell, style="F")
            else:
                c += 1


def _wrap(pdf: FPDF, text: str, width: float) -> list[str]:
    """Split text into lines that fit the width (at the current font): at spaces, and
    inside a word only when the word alone is too long (an IMEI on a narrow label)."""
    out, line = [], ""
    for word in text.split(" "):
        candidate = f"{line} {word}" if line else word
        if pdf.get_string_width(candidate) <= width:
            line = candidate
            continue
        if line:
            out.append(line)
        while pdf.get_string_width(word) > width and len(word) > 1:
            cut = len(word)
            while cut > 1 and pdf.get_string_width(word[:cut]) > width:
                cut -= 1
            out.append(word[:cut])
            word = word[cut:]
        line = word
    if line:
        out.append(line)
    return out


LINE = 0.42  # line height in mm per font point (≈ 1.2 × 1 pt)
MIN_PT, MAX_PT = 4.5, 9.0


def _layout(pdf: FPDF, rows: list[tuple[str, bool]], width: float, height: float):
    """The largest font size at which every row, wrapped, fits the box; and the lines."""
    size = MAX_PT
    while True:
        lines = []
        for text, bold in rows:
            pdf.set_font("ui", "B" if bold else "", size)
            lines += [(part, bold) for part in _wrap(pdf, text, width)]
        if len(lines) * size * LINE <= height or size <= MIN_PT:
            return size, lines
        size -= 0.25


def _arrange(pdf: FPDF, d: dict, opts: dict, x0: float, y0: float, w: float, h: float) -> dict:
    """Where everything goes on one sticker (mm). Used for printing and for the preview,
    so the preview shows exactly what prints."""
    pad = 1.6
    side = min(h - 2 * pad, w * (0.40 if w < 50 else 0.45))
    qr = {"x": x0 + pad, "y": y0 + (h - side) / 2, "side": side, "data": qr_text(d, opts["qr"])}
    tx = x0 + pad + side + 1.6
    tw = x0 + w - pad - tx
    size, lines = _layout(pdf, lines_for(d, opts), tw, h - 2 * pad)
    # Whatever still does not fit at the smallest size is left out (the QR code has it).
    lines = lines[:max(1, int((h - 2 * pad) / (size * LINE)))]
    y = y0 + max(pad, (h - len(lines) * size * LINE) / 2)
    placed = []
    for text, bold in lines:
        placed.append({"x": tx, "y": y, "w": tw, "h": size * LINE, "size": size, "bold": bold, "text": text})
        y += size * LINE
    return {"qr": qr, "lines": placed}


def _draw_label(pdf: FPDF, d: dict, opts: dict, x0: float, y0: float, w: float, h: float) -> None:
    a = _arrange(pdf, d, opts, x0, y0, w, h)
    _draw_qr(pdf, a["qr"]["data"], a["qr"]["x"], a["qr"]["y"], a["qr"]["side"])
    pdf.set_text_color(0, 0, 0)
    for ln in a["lines"]:
        pdf.set_font("ui", "B" if ln["bold"] else "", ln["size"])
        pdf.set_xy(ln["x"], ln["y"])
        pdf.cell(ln["w"], ln["h"], ln["text"])


def build(devices: list[dict], opts: dict) -> Path:
    """One PDF with a sticker for each device. Label printers: one page per sticker.
    A4: 24 stickers per sheet."""
    if not devices:
        raise ValueError("no devices")
    pdf = _Labels(opts["size"])
    w, h = SIZES[opts["size"]]
    if opts["size"] == "a4":
        cols, rows = A4_GRID
        left, top = (210 - cols * w) / 2, (297 - rows * h) / 2
        for i, d in enumerate(devices):
            if i % (cols * rows) == 0:
                pdf.add_page()
            k = i % (cols * rows)
            _draw_label(pdf, d, opts, left + (k % cols) * w, top + (k // cols) * h, w, h)
    else:
        for d in devices:
            pdf.add_page()
            _draw_label(pdf, d, opts, 0, 0, w, h)
    if len(devices) == 1:
        d = devices[0]
        model = t(d.get("model_name") or "") or d.get("model") or "iPhone"
        name = f"{t('Наклейка')} {model} {d.get('serial') or (d.get('id') or '')[:12]}"
    else:
        name = f"{t('Наклейки')} {datetime.now().strftime('%Y-%m-%d %H-%M')} ({len(devices)})"
    name = re.sub(r'[\\/:*?"<>|\r\n\t]+', " ", name).strip()[:90] + ".pdf"
    path = labels_dir() / name
    pdf.output(str(path))
    return path


def make(device_ids: list[str], opts: dict, open_after: bool = True) -> Path | None:
    data = history.export()
    devices = [data[i] for i in device_ids if i in data]
    if not devices:
        return None
    path = build(devices, opts)
    if open_after:
        open_file(path)
    return path


SAMPLE = {"id": "sample", "serial": "F2LXK0ABCD12", "model_name": "iPhone 15 Pro", "capacity": "256 ГБ",
          "imei": "356789012345678", "ios": "18.6", "battery": 91, "last_seen": "",
          "note": "A-12", "events": [{"action": "Диагностика", "result": "ok"}]}


def preview(opts: dict, device: dict | None = None) -> dict:
    """One sticker laid out for the preview in Settings (the latest phone from the history,
    or a sample one): its size, the QR code's squares and each text line, in mm, so the
    window can draw it. Nothing is saved."""
    d = dict(device or SAMPLE)
    if not d.get("last_seen"):
        d["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if opts.get("note") and not d.get("note"):
        d["note"] = "A-12"
    size = opts.get("size") if opts.get("size") in SIZES else DEFAULTS["size"]
    w, h = SIZES[size]  # for the A4 sheet: one of its stickers
    pdf = _Labels("a4one" if size == "a4" else size)
    pdf.add_page()
    a = _arrange(pdf, d, {**DEFAULTS, **opts}, 0, 0, w, h)
    matrix = ["".join("1" if c else "0" for c in row) for row in segno.make(a["qr"]["data"] or "-", error="m").matrix]
    a["qr"]["matrix"] = matrix
    del a["qr"]["data"]
    for ln in a["lines"]:
        ln.update({k: round(ln[k], 3) for k in ("x", "y", "w", "h", "size")})
    return {"w": w, "h": h, **a}
