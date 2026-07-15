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
LABEL_HEIGHT = 100 * mm


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
    out = path or (settings.TEMP_DIR / f"{item.numero}.pdf")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(out), pagesize=(LABEL_WIDTH, LABEL_HEIGHT))
    w = LABEL_WIDTH
    y = LABEL_HEIGHT - 5 * mm

    logo = settings.logo_path
    if logo.exists():
        try:
            c.drawImage(str(logo), 4 * mm, y - 10 * mm, 12 * mm, 10 * mm, mask="auto")
        except Exception:
            pass

    c.setFillColorRGB(0.18, 0.18, 0.18)
    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(w - 4 * mm, y - 4 * mm, "NGOKAF LUGGAGE")
    y -= 12 * mm

    c.setStrokeColorRGB(0.89, 0.85, 0.76)
    c.setLineWidth(0.4)
    c.line(4 * mm, y, w - 4 * mm, y)
    y -= 5 * mm

    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(w / 2, y, "LUGGAGE ID")
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(w / 2, y, item.numero)
    y -= 5 * mm
    c.line(4 * mm, y, w - 4 * mm, y)
    y -= 5 * mm

    def row(label: str, value: str):
        nonlocal y
        c.setFont("Helvetica-Bold", 7)
        c.setFillColorRGB(0.18, 0.18, 0.18)
        c.drawString(4 * mm, y, label)
        c.drawRightString(w - 4 * mm, y, value)
        y -= 3 * mm
        c.setStrokeColorRGB(0.89, 0.85, 0.76)
        c.line(4 * mm, y, w - 4 * mm, y)
        y -= 4 * mm

    route = ""
    if item.route:
        d = item.route.ville_depart[:3].upper()
        a = item.route.ville_arrivee[:3].upper()
        route = f"{d} > {a}"
    row("ROUTE", route)
    row("POIDS", f"{float(item.poids):.1f} KG")
    row("VOYAGEUR", item.sender_name.upper()[:18])
    row("TEL", (item.sender_phone or "")[:18])
    row("PRIX", f"{float(item.total):.0f} FC")

    if item.fragile:
        c.setFillColorRGB(0, 0, 0)
        c.rect(4 * mm, y - 6 * mm, w - 8 * mm, 6 * mm, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(w / 2, y - 4.2 * mm, "⚠ FRAGILE")
        y -= 9 * mm

    try:
        bc = _barcode_image(item.barcode)
        c.drawImage(bc, 5 * mm, y - 12 * mm, w - 10 * mm, 12 * mm, mask="auto")
        y -= 14 * mm
    except Exception:
        y -= 2 * mm

    c.setFillColorRGB(0.18, 0.18, 0.18)
    c.setFont("Helvetica", 6)
    c.drawCentredString(w / 2, y, item.barcode)
    y -= 4 * mm
    c.setFillColorRGB(0.43, 0.43, 0.43)
    c.setFont("Helvetica", 5)
    terminal = settings.TERMINAL_NAME[:10]
    c.drawCentredString(
        w / 2,
        y,
        f"DATE: {item.created_at.strftime('%d/%m/%Y')} | TERMINAL: {terminal}",
    )

    c.showPage()
    c.save()
    return out


def print_luggage_label(item) -> Path:
    pdf_path = generate_luggage_label_pdf(item)
    try:
        import os

        os.startfile(str(pdf_path), "print")  # type: ignore[attr-defined]
    except Exception:
        pass
    return pdf_path
