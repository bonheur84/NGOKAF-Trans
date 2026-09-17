"""Thermal luggage label 58mm."""
from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

import barcode
from barcode.writer import ImageWriter
import qrcode
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from config.settings import settings


LABEL_WIDTH = 58 * mm
# Dynamic height helps with continuous rolls. Set a max height for typical use:
LABEL_HEIGHT = 140 * mm


def _barcode_image(code: str):
    Code128 = barcode.get_barcode_class("code128")
    buf = io.BytesIO()
    Code128(code, writer=ImageWriter()).write(
        buf,
        options={"write_text": False, "module_height": 10, "quiet_zone": 1},
    )
    buf.seek(0)
    return ImageReader(buf)


def generate_luggage_label_pdf(item, path: Path | None = None) -> Path:
    out = path or (settings.TEMP_DIR / f"luggage_{item.numero}.pdf")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(out), pagesize=(LABEL_WIDTH, LABEL_HEIGHT))
    w = LABEL_WIDTH
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, LABEL_WIDTH, LABEL_HEIGHT, fill=1, stroke=0)

    margin = 4 * mm
    content_width = w - 2 * margin

    def centered_fit(text: str, y_pos: float, *, size: float, font: str = "Helvetica-Bold") -> None:
        """Draw centred text without letting a long code or name overflow."""
        value = str(text or "—")
        fitted_size = size
        while fitted_size > 6 and pdfmetrics.stringWidth(value, font, fitted_size) > content_width:
            fitted_size -= 0.5
        c.setFont(font, fitted_size)
        c.drawCentredString(w / 2, y_pos, value)

    def separator(y_pos: float) -> None:
        c.setStrokeColorRGB(0.75, 0.75, 0.75)
        c.setLineWidth(0.45)
        c.line(margin, y_pos, w - margin, y_pos)

    # One adhesive label per luggage item. No customer receipt is printed.
    y = LABEL_HEIGHT - 5 * mm

    # 1. HEADER (Logo & Brand)
    logo = settings.logo_path
    if logo.exists():
        try:
            c.drawImage(str(logo), margin, y - 10 * mm, 12 * mm, 10 * mm, mask="auto")
        except Exception:
            pass

    c.setFillColorRGB(0.05, 0.05, 0.05)
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(w - margin, y - 3.5 * mm, "NGOKAF TRANS")
    c.setFont("Helvetica-Bold", 6.5)
    c.drawRightString(w - margin, y - 7.5 * mm, "ÉTIQUETTE BAGAGE")
    y -= 12 * mm

    # 2. Prominent, scan-friendly baggage code.
    c.setStrokeColorRGB(0.05, 0.05, 0.05)
    c.setLineWidth(1.2)
    c.roundRect(margin, y - 17 * mm, content_width, 17 * mm, 2 * mm, fill=0, stroke=1)
    c.setFillColorRGB(0.05, 0.05, 0.05)
    c.setFont("Helvetica-Bold", 6.5)
    c.drawCentredString(w / 2, y - 5 * mm, "CODE BAGAGE")
    centered_fit(item.numero, y - 12.5 * mm, size=16)
    y -= 21 * mm

    # 3. Details use one clearly aligned line per item: label left, value right.
    def field(label: str, value: str, *, value_size: float = 9) -> None:
        nonlocal y
        label_width = pdfmetrics.stringWidth(label, "Helvetica-Bold", 7)
        value = str(value or "—")
        max_value_width = content_width - label_width - 5 * mm
        fitted_size = value_size
        while fitted_size > 6 and pdfmetrics.stringWidth(value, "Helvetica-Bold", fitted_size) > max_value_width:
            fitted_size -= 0.5
        c.setFillColorRGB(0.38, 0.38, 0.38)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(margin, y, label)
        c.setFillColorRGB(0.05, 0.05, 0.05)
        c.setFont("Helvetica-Bold", fitted_size)
        c.drawRightString(w - margin, y, value)
        y -= 6 * mm

    route = getattr(item, "route_label", "") or ""
    if item.route:
        d = item.route.ville_depart.upper()
        a = item.route.ville_arrivee.upper()
        route = f"{d} ➔ {a}"
    field("TRAJET", route.upper(), value_size=9)
    field("BILLET", getattr(item, "ticket_numero", "") or "—", value_size=9)
    bus_code = getattr(item, "bus_code", "") or (item.bus.code if item.bus else "")
    field("BUS", bus_code or "—", value_size=9)
    field("PASSAGER", item.sender_name.upper(), value_size=10)
    field("POIDS", f"{float(item.poids):.1f} KG", value_size=9)
    field("TOTAL", f"{float(item.total):.0f} FC", value_size=10)

    # 4. FRAGILE ALERT
    if item.fragile:
        y -= 1 * mm
        c.setFillColorRGB(0, 0, 0)
        c.rect(4 * mm, y - 7 * mm, w - 8 * mm, 7 * mm, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(w / 2, y - 5 * mm, "⚠ FRAGILE ⚠")
        y -= 9 * mm
    else:
        y -= 2 * mm

    y -= 4 * mm

    # 5. BARCODE
    try:
        bc = _barcode_image(item.barcode)
        c.drawImage(bc, margin, y - 12 * mm, content_width, 12 * mm, mask="auto")
        y -= 13.5 * mm
    except Exception:
        y -= 2 * mm

    c.setFillColorRGB(0.05, 0.05, 0.05)
    centered_fit(item.barcode, y, size=7, font="Helvetica")
    y -= 5 * mm

    # 6. FOOTER
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.setFont("Helvetica", 5.5)
    terminal = settings.TERMINAL_NAME[:15]
    date_str = item.created_at.strftime('%d/%m/%y %H:%M')
    c.drawCentredString(w / 2, y, f"DATE: {date_str} | TERMINAL: {terminal}")

    y -= 3 * mm
    separator(y)

    c.save()
    return out


def print_luggage_label(item, printer_name: str | None = None) -> Path:
    pdf_path = generate_luggage_label_pdf(item)
    printed = False
    try:
        from reports.ticket_80mm import print_pdf_direct
        printed = print_pdf_direct(pdf_path, printer_name=printer_name)
    except Exception:
        printed = False

    if not printed:
        try:
            import os
            os.startfile(str(pdf_path))
        except Exception:
            pass
    return pdf_path
