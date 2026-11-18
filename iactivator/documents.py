"""Service paperwork as PDF: an intake act (phone received), a handover act (phone given
back) and a warranty certificate. Built from the device's history entry, the shop details
saved in Settings, and a few fields the user fills before printing. Reuses the report's
fonts and logo so everything looks the same.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path

from fpdf import FPDF

from .core import app_data_dir
from .i18n import t
from .report import FONTS, INK, LINE, MUTED, _logo, open_file

FOLDER = "Документы"
KINDS = ("intake", "handover", "warranty")


def documents_dir() -> Path:
    d = app_data_dir() / FOLDER
    d.mkdir(parents=True, exist_ok=True)
    return d


def _capacity(text) -> str:
    m = re.fullmatch(r"\s*(\d+)\s*(ГБ|ТБ|GB|TB)\s*", str(text or ""))
    return t("{n} ТБ" if m.group(2) in ("ТБ", "TB") else "{n} ГБ", n=m.group(1)) if m else str(text or "")


class _Doc(FPDF):
    def __init__(self):
        super().__init__(format="A4")
        for regular, bold in FONTS:
            if Path(regular).exists() and Path(bold).exists():
                self.add_font("ui", "", regular)
                self.add_font("ui", "B", bold)
                break
        else:
            raise RuntimeError(t("Не найден шрифт с кириллицей для PDF"))
        self.set_margins(18, 16, 18)
        self.set_auto_page_break(True, 18)

    def footer(self):
        self.set_y(-13)
        self.set_font("ui", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 5, t("Создано в iActivator"), align="L")


def _width(pdf: FPDF) -> float:
    return pdf.w - pdf.l_margin - pdf.r_margin


def _title(kind: str) -> str:
    return {"intake": t("Акт приёма устройства"), "handover": t("Акт выдачи устройства"),
            "warranty": t("Гарантийный талон")}.get(kind, t("Документ"))


def _header(pdf: _Doc, shop: dict, kind: str, number: str, date: str) -> None:
    _logo(pdf, pdf.l_margin, pdf.get_y(), 16)
    pdf.set_xy(pdf.l_margin + 20, pdf.get_y() + 1)
    pdf.set_font("ui", "B", 13)
    pdf.set_text_color(*INK)
    pdf.cell(_width(pdf) - 20, 6, shop.get("name") or "iActivator", new_x="LMARGIN", new_y="NEXT")
    sub = " · ".join(x for x in (shop.get("phone"), shop.get("address")) if x)
    if sub:
        pdf.set_x(pdf.l_margin + 20)
        pdf.set_font("ui", "", 9)
        pdf.set_text_color(*MUTED)
        pdf.cell(_width(pdf) - 20, 5, sub, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("ui", "B", 15)
    pdf.set_text_color(*INK)
    title = _title(kind)
    if number:
        title += f" № {number}"
    pdf.cell(_width(pdf), 8, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("ui", "", 9.5)
    pdf.set_text_color(*MUTED)
    pdf.cell(_width(pdf), 6, f"{t('Дата')}: {date}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_draw_color(*LINE)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(5)


def _row(pdf: _Doc, label: str, value: str) -> None:
    if value in (None, ""):
        return
    pdf.set_font("ui", "", 9)
    pdf.set_text_color(*MUTED)
    pdf.cell(42, 6, label)
    pdf.set_font("ui", "B", 10.5)
    pdf.set_text_color(*INK)
    pdf.multi_cell(_width(pdf) - 42, 6, str(value), new_x="LMARGIN", new_y="NEXT")


def _battery(d: dict) -> str:
    b = d.get("battery")
    return f"{min(int(b), 100)}%" if isinstance(b, (int, float)) else ""


def _device_rows(pdf: _Doc, d: dict) -> None:
    model = t(d.get("model_name") or "") or d.get("model") or "iPhone"
    _row(pdf, t("Модель"), model + (f", {_capacity(d['capacity'])}" if d.get("capacity") else ""))
    _row(pdf, t("Серийный №"), d.get("serial"))
    _row(pdf, "IMEI", d.get("imei"))
    if d.get("imei2"):
        _row(pdf, "IMEI 2", d.get("imei2"))
    _row(pdf, "iOS", d.get("ios"))
    _row(pdf, t("Батарея"), _battery(d))


def _signatures(pdf: _Doc, left: str, right: str) -> None:
    pdf.ln(10)
    y = pdf.get_y()
    half = _width(pdf) / 2
    for i, label in enumerate((left, right)):
        x = pdf.l_margin + i * half
        pdf.line(x, y + 8, x + half - 10, y + 8)
        pdf.set_xy(x, y + 9)
        pdf.set_font("ui", "", 8.5)
        pdf.set_text_color(*MUTED)
        pdf.cell(half - 10, 4, label)


def build(kind: str, device: dict, shop: dict, fields: dict) -> Path:
    if kind not in KINDS:
        raise ValueError("unknown document kind")
    now = datetime.now()
    pdf = _Doc()
    pdf.add_page()
    _header(pdf, shop or {}, kind, str(fields.get("number", "")).strip(), now.strftime("%d.%m.%Y %H:%M"))
    _device_rows(pdf, device)
    if fields.get("customer"):
        _row(pdf, t("Клиент"), fields["customer"])
    if fields.get("defects"):
        _row(pdf, t("Состояние / дефекты"), fields["defects"])
    if kind == "handover" and fields.get("work"):
        _row(pdf, t("Выполненные работы"), fields["work"])
    if fields.get("price"):
        _row(pdf, t("Стоимость"), fields["price"])

    if kind == "warranty":
        months = fields.get("warranty_months") or shop.get("warranty_months") or 0
        try:
            months = int(months)
        except (TypeError, ValueError):
            months = 0
        if months:
            until = (now + timedelta(days=30 * months)).strftime("%d.%m.%Y")
            _row(pdf, t("Гарантия"), t("{n} мес. (до {date})", n=months, date=until))
        pdf.ln(3)
        pdf.set_font("ui", "", 8.5)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(_width(pdf), 4.4, t(
            "Гарантия не распространяется на механические повреждения, попадание жидкости и "
            "следы самостоятельного ремонта. Сохраняйте этот талон."), new_x="LMARGIN", new_y="NEXT")

    left = {"intake": t("Сдал (клиент)"), "handover": t("Получил (клиент)"), "warranty": t("Клиент")}[kind]
    right = {"intake": t("Принял (сервис)"), "handover": t("Выдал (сервис)"), "warranty": t("Сервис")}[kind]
    _signatures(pdf, left, right)

    name = f"{_title(kind)} {(device.get('serial') or (device.get('id') or '')[:10])} {now.strftime('%Y-%m-%d %H-%M')}"
    name = re.sub(r'[\\/:*?"<>|\r\n\t]+', " ", name).strip()[:90] + ".pdf"
    path = documents_dir() / name
    pdf.output(str(path))
    return path


def make(kind: str, device: dict, shop: dict, fields: dict, open_after: bool = True) -> Path:
    path = build(kind, device, shop, fields)
    if open_after:
        open_file(path)
    return path
