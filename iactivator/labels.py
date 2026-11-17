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
DEFAULTS = {"enabled": False, "size": "40x30", "qr": "text", "note": False}


def options(ui: dict) -> dict:
    """The sticker settings with defaults for anything missing or not allowed."""
    o = dict(DEFAULTS)
    saved = ui.get("labels") if isinstance(ui.get("labels"), dict) else {}
    if isinstance(saved.get("enabled"), bool):
        o["enabled"] = saved["enabled"]
    if saved.get("size") in SIZES:
        o["size"] = saved["size"]
    if saved.get("qr") in QR_MODES:
        o["qr"] = saved["qr"]
    if isinstance(saved.get("note"), bool):
        o["note"] = saved["note"]
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


def lines_for(d: dict, with_note: bool) -> list[tuple[str, bool]]:
    """What is printed next to the QR code: (text, bold)."""
    model = t(d.get("model_name") or "") or d.get("model") or "iPhone"
    out = [(model + (f" · {_capacity(d['capacity'])}" if d.get("capacity") else ""), True)]
    if d.get("serial"):
        out.append((f"S/N {d['serial']}", False))
    if d.get("imei"):
        out.append((f"IMEI {d['imei']}", False))
    extra = []
    if isinstance(d.get("battery"), (int, float)):
        extra.append(f"{t('Батарея')} {min(int(d['battery']), 100)}%")
    if d.get("ios"):
        extra.append(f"iOS {d['ios']}")
    if extra:
        out.append((" · ".join(extra), False))
    v = verdict(d)
    date = (d.get("last_seen") or "")[:10]
    if v or date:
        out.append((" · ".join(x for x in (v, date) if x), bool(v)))
    if with_note and d.get("note"):
        out.append((d["note"].replace("\n", " "), False))
    return out


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
        w, h = SIZES[size]
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


def _draw_label(pdf: FPDF, d: dict, opts: dict, x0: float, y0: float, w: float, h: float) -> None:
    pad = 1.6
    side = min(h - 2 * pad, w * (0.40 if w < 50 else 0.45))
    _draw_qr(pdf, qr_text(d, opts["qr"]), x0 + pad, y0 + (h - side) / 2, side)
    tx = x0 + pad + side + 1.6
    tw = x0 + w - pad - tx
    size, lines = _layout(pdf, lines_for(d, opts["note"]), tw, h - 2 * pad)
    # Whatever still does not fit at the smallest size is left out (the QR code has it).
    lines = lines[:max(1, int((h - 2 * pad) / (size * LINE)))]
    y = y0 + max(pad, (h - len(lines) * size * LINE) / 2)
    pdf.set_text_color(0, 0, 0)
    for text, bold in lines:
        pdf.set_font("ui", "B" if bold else "", size)
        pdf.set_xy(tx, y)
        pdf.cell(tw, size * LINE, text)
        y += size * LINE


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
