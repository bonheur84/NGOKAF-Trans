"""Thermal ticket 80mm — ReportLab + optional Qt print."""
from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

import qrcode
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from config.settings import settings
from utils.formatters import MONTHS_FR, format_fc


TICKET_WIDTH = 80 * mm
# Height grows with content; typical receipt ~200mm
TICKET_HEIGHT = 200 * mm


def _qr_image(payload: str):
    img = qrcode.make(payload, border=1)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def generate_ticket_pdf(ticket, path: Path | None = None) -> Path:
    """Generate 80mm passenger ticket PDF matching TICKET1 design."""
    out = path or (settings.TEMP_DIR / f"{ticket.numero}.pdf")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(out), pagesize=(TICKET_WIDTH, TICKET_HEIGHT))
    w = TICKET_WIDTH
    y = TICKET_HEIGHT - 8 * mm

    # Logo
    logo = settings.logo_path
    if logo.exists():
        try:
            c.drawImage(str(logo), (w - 28 * mm) / 2, y - 22 * mm, 28 * mm, 22 * mm, mask="auto")
            y -= 24 * mm
        except Exception:
            y -= 2 * mm
    else:
        y -= 2 * mm

    c.setFillColorRGB(0.18, 0.18, 0.18)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(w / 2, y, settings.AGENCY_NAME)
    y -= 5 * mm
    c.setFont("Helvetica", 8)
    c.drawCentredString(w / 2, y, "Agence Centrale - Douala")
    y -= 4 * mm
    c.drawCentredString(w / 2, y, f"{settings.AGENCY_ADDRESS}")
    y -= 6 * mm

    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.43, 0.43, 0.43)
    c.drawCentredString(w / 2, y, "NUMÉRO DE BILLET")
    y -= 7 * mm
    c.setFillColorRGB(0.18, 0.18, 0.18)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(w / 2, y, ticket.numero)
    y -= 5 * mm

    # Divider
    c.setStrokeColorRGB(0.89, 0.85, 0.76)
    c.setLineWidth(0.5)
    c.line(6 * mm, y, w - 6 * mm, y)
    y -= 6 * mm

    # Date & seat — date de voyage + heure de départ
    travel_dt = datetime.combine(ticket.travel_date, ticket.route.heure_depart)
    printed_at = ticket.created_at or datetime.now()
    date_str = (
        f"{travel_dt.day:02d} {MONTHS_FR[travel_dt.month]} {travel_dt.year} "
        f"- {travel_dt.strftime('%H:%M')}"
    )
    c.setFont("Helvetica", 6)
    c.setFillColorRGB(0.43, 0.43, 0.43)
    c.drawString(6 * mm, y, "DATE & HEURE DÉPART")
    c.drawRightString(w - 6 * mm, y, "SIÈGE")
    y -= 5 * mm
    c.setFillColorRGB(0.18, 0.18, 0.18)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(6 * mm, y, date_str)
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(w - 6 * mm, y, str(ticket.seat_number))
    y -= 4 * mm
    c.setFont("Helvetica", 6)
    c.setFillColorRGB(0.43, 0.43, 0.43)
    c.drawString(
        6 * mm,
        y,
        f"Émis le {printed_at.strftime('%d/%m/%Y à %H:%M')}",
    )
    y -= 5 * mm

    c.setStrokeColorRGB(0.89, 0.85, 0.76)
    c.line(6 * mm, y, w - 6 * mm, y)
    y -= 5 * mm

    c.setFont("Helvetica", 6)
    c.setFillColorRGB(0.43, 0.43, 0.43)
    c.drawString(6 * mm, y, "TRAJET")
    y -= 5 * mm
    c.setFillColorRGB(0.18, 0.18, 0.18)
    c.setFont("Helvetica-Bold", 11)
    depart = ticket.route.ville_depart.upper()
    arrivee = ticket.route.ville_arrivee.upper()
    c.drawCentredString(w / 2, y, f"{depart}  →  {arrivee}")
    y -= 5 * mm

    c.setStrokeColorRGB(0.89, 0.85, 0.76)
    c.line(6 * mm, y, w - 6 * mm, y)
    y -= 5 * mm

    c.setFont("Helvetica", 6)
    c.setFillColorRGB(0.43, 0.43, 0.43)
    c.drawString(6 * mm, y, "PASSAGER")
    y -= 5 * mm
    c.setFillColorRGB(0.18, 0.18, 0.18)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(w / 2, y, ticket.passenger_name.upper())
    y -= 8 * mm

    # Total box
    box_h = 14 * mm
    c.setFillColorRGB(0, 0, 0)
    c.rect(6 * mm, y - box_h, w - 12 * mm, box_h, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(w / 2, y - 5 * mm, "TOTAL PAYÉ")
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(w / 2, y - 11 * mm, format_fc(ticket.price))
    y -= box_h + 6 * mm

    # QR
    qr = _qr_image(ticket.qr_payload)
    qr_size = 28 * mm
    c.drawImage(qr, (w - qr_size) / 2, y - qr_size, qr_size, qr_size, mask="auto")
    y -= qr_size + 5 * mm

    c.setFillColorRGB(0.18, 0.18, 0.18)
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(w / 2, y, "*** BON VOYAGE ***")
    y -= 6 * mm
    c.setFont("Helvetica", 6)
    c.setFillColorRGB(0.43, 0.43, 0.43)
    c.drawCentredString(
        w / 2,
        y,
        "Ticket non remboursable 2h avant le départ.",
    )
    y -= 3 * mm
    c.drawCentredString(
        w / 2,
        y,
        "Présentez-vous 30 min avant l'embarquement.",
    )

    c.showPage()
    c.save()
    return out


def print_ticket_windows(ticket) -> Path:
    """Generate PDF and send to default printer on Windows if possible."""
    pdf_path = generate_ticket_pdf(ticket)
    try:
        import os

        os.startfile(str(pdf_path), "print")  # type: ignore[attr-defined]
    except Exception:
        pass
    return pdf_path
