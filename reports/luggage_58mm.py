"""Thermal luggage label 58mm."""
from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

import barcode
from barcode.writer import ImageWriter
import qrcode
from reportlab.lib.units import mm
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

    def draw_dashed_line(y_pos):
        c.setStrokeColorRGB(0.5, 0.5, 0.5)
        c.setLineWidth(0.8)
        c.setDash([2, 2])
        c.line(4 * mm, y_pos, w - 4 * mm, y_pos)
        c.setDash([])

    # One adhesive label per luggage item.  No customer receipt is printed.
    y = LABEL_HEIGHT - 4 * mm

    # 1. HEADER (Logo & Brand)
    logo = settings.logo_path
    if logo.exists():
        try:
            c.drawImage(str(logo), 4 * mm, y - 10 * mm, 12 * mm, 10 * mm, mask="auto")
        except Exception:
            pass

    c.setFillColorRGB(0.05, 0.05, 0.05)
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(w - 4 * mm, y - 4 * mm, "NGOKAF LUGGAGE")
    c.setFont("Helvetica", 6)
    c.drawRightString(w - 4 * mm, y - 8 * mm, "ÉTIQUETTE À COLLER")
    y -= 12 * mm

    draw_dashed_line(y)
    y -= 4 * mm

    # 2. LUGGAGE ID
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(w / 2, y, item.numero)
    y -= 5 * mm
    draw_dashed_line(y)
    y -= 4 * mm

    # 3. DETAILS
    def row(label: str, value: str, val_size=8, bold=True):
        nonlocal y
        c.setFont("Helvetica", 6.5)
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.drawString(4 * mm, y, label)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", val_size)
        c.setFillColorRGB(0.05, 0.05, 0.05)
        c.drawRightString(w - 4 * mm, y, value)
        y -= 5 * mm

    route = getattr(item, "route_label", "") or ""
    if item.route:
        d = item.route.ville_depart.upper()
        a = item.route.ville_arrivee.upper()
        route = f"{d} ➔ {a}"
    row("TRAJET", route, val_size=9)
    row("BILLET", getattr(item, "ticket_numero", "") or "—", val_size=9)
    bus_code = getattr(item, "bus_code", "") or (item.bus.code if item.bus else "")
    row("BUS", bus_code or "—", val_size=8)

    row("PASSAGER", item.sender_name.upper()[:16], val_size=8)

    # Poids & Colis
    row("POIDS", f"{float(item.poids):.1f} KG", val_size=9)

    # Prix
    row("TOTAL", f"{float(item.total):.0f} FC", val_size=10)

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

    draw_dashed_line(y)
    y -= 4 * mm

    # 5. BARCODE
    try:
        bc = _barcode_image(item.barcode)
        c.drawImage(bc, 4 * mm, y - 12 * mm, w - 8 * mm, 12 * mm, mask="auto")
        y -= 14 * mm
    except Exception:
        y -= 2 * mm

    c.setFillColorRGB(0.05, 0.05, 0.05)
    c.setFont("Helvetica", 7)
    c.drawCentredString(w / 2, y, item.barcode)
    y -= 5 * mm

    # 6. FOOTER
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.setFont("Helvetica", 5.5)
    terminal = settings.TERMINAL_NAME[:15]
    date_str = item.created_at.strftime('%d/%m/%y %H:%M')
    c.drawCentredString(w / 2, y, f"DATE: {date_str} | TERMINAL: {terminal}")

    y -= 3 * mm
    draw_dashed_line(y)

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
