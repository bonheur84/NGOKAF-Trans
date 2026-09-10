"""Thermal ticket 80mm — ReportLab + direct Qt physical printing."""
from __future__ import annotations

import io
import logging
from datetime import datetime
from pathlib import Path

import qrcode
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from config.settings import settings
from utils.formatters import MONTHS_FR, format_fc

logger = logging.getLogger(__name__)

TICKET_WIDTH = 80 * mm
# Typical 80mm receipt height is dynamic, but we set a standard max and let the printer cut
TICKET_HEIGHT = 240 * mm


def _qr_image(payload: str):
    img = qrcode.make(payload, border=1)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def generate_ticket_pdf(ticket, path: Path | None = None) -> Path:
    """Generate 80mm passenger ticket PDF with brand logo and complete layout."""
    out = path or (settings.TEMP_DIR / f"{ticket.numero}.pdf")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(out), pagesize=(TICKET_WIDTH, TICKET_HEIGHT))
    w = TICKET_WIDTH
    y = TICKET_HEIGHT - 5 * mm

    # 1. HEADER (Logo & Agency Info)
    logo = settings.logo_path
    if logo.exists():
        try:
            logo_w = 28 * mm
            logo_h = 30 * mm
            c.drawImage(
                str(logo),
                (w - logo_w) / 2,
                y - logo_h,
                logo_w,
                logo_h,
                mask="auto",
            )
            y -= (logo_h + 4 * mm)
        except Exception:
            y -= 2 * mm
    else:
        y -= 2 * mm

    # Fetch Agency Settings dynamically
    agency_name = settings.AGENCY_NAME
    agency_address = settings.AGENCY_ADDRESS
    agency_phone = settings.AGENCY_PHONE
    agency_id = getattr(ticket, "agency_id", None)
    
    try:
        from database.session import get_session
        from services import settings_service
        session = get_session()
        agency_name = settings_service.get_setting(session, "agency_name", settings.AGENCY_NAME, agency_id=agency_id)
        agency_address = settings_service.get_setting(session, "agency_address", settings.AGENCY_ADDRESS, agency_id=agency_id)
        agency_phone = settings_service.get_setting(session, "agency_phone", settings.AGENCY_PHONE, agency_id=agency_id)
        session.close()
    except Exception:
        pass

    c.setFillColorRGB(0.05, 0.05, 0.05)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(w / 2, y, agency_name.upper())
    y -= 5 * mm
    
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.drawCentredString(w / 2, y, agency_address)
    y -= 4 * mm
    if agency_phone:
        c.drawCentredString(w / 2, y, f"Tél: {agency_phone}")
        y -= 4 * mm

    y -= 2 * mm

    def draw_dashed_line(y_pos):
        c.setStrokeColorRGB(0.5, 0.5, 0.5)
        c.setLineWidth(0.8)
        c.setDash([2, 2])
        c.line(4 * mm, y_pos, w - 4 * mm, y_pos)
        c.setDash([]) # reset

    draw_dashed_line(y)
    y -= 5 * mm

    # 2. TICKET INFO (Number & Status)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(0.0, 0.0, 0.0)
    c.drawCentredString(w / 2, y, "BILLET DE TRANSPORT")
    y -= 6 * mm
    
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(w / 2, y, ticket.numero)
    y -= 6 * mm

    draw_dashed_line(y)
    y -= 5 * mm

    # Helper for two-column rows
    def row2(lbl1, val1, lbl2, val2, val_font="Helvetica-Bold", val_size=9):
        nonlocal y
        c.setFont("Helvetica", 6)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawString(4 * mm, y, lbl1)
        c.drawRightString(w - 4 * mm, y, lbl2)
        y -= 3.5 * mm
        c.setFont(val_font, val_size)
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.drawString(4 * mm, y, val1)
        c.drawRightString(w - 4 * mm, y, val2)
        y -= 5 * mm

    # 3. VOYAGE INFO (Crucial part)
    depart = ticket.route.ville_depart.upper() if (ticket.route and getattr(ticket.route, "ville_depart", None)) else "—"
    arrivee = ticket.route.ville_arrivee.upper() if (ticket.route and getattr(ticket.route, "ville_arrivee", None)) else "—"
    
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawCentredString(w / 2, y, "TRAJET")
    y -= 4.5 * mm
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0.05, 0.05, 0.05)
    c.drawCentredString(w / 2, y, f"{depart} ➔ {arrivee}")
    y -= 6 * mm

    # Dates
    t_date = ticket.travel_date
    date_voyage_str = f"{t_date.day:02d} {MONTHS_FR[t_date.month]} {t_date.year}"
    heure_actuelle = datetime.now().strftime('%H:%M')
    
    row2("DATE DU VOYAGE", date_voyage_str.upper(), "HEURE ACT.", heure_actuelle, val_size=10)
    
    # 4. BUS & SEAT
    bus_info = "—"
    if ticket.bus:
        bus_info = ticket.bus.code
        if ticket.bus.plaque:
            bus_info += f" ({ticket.bus.plaque})"
            
    c.setFillColorRGB(0, 0, 0)
    c.rect(4 * mm, y - 9 * mm, w - 8 * mm, 9 * mm, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    
    c.setFont("Helvetica-Bold", 8)
    c.drawString(6 * mm, y - 6 * mm, f"BUS: {bus_info}")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(w - 6 * mm, y - 6 * mm, f"SIÈGE : {ticket.seat_number}")
    y -= 13 * mm

    # 5. PASSENGER INFO
    pass_phone = getattr(ticket, "phone", "")
    row2("PASSAGER", ticket.passenger_name.upper()[:20], "TÉLÉPHONE", pass_phone)

    # 6. PRICE & EMISSION
    draw_dashed_line(y)
    y -= 5 * mm
    
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(4 * mm, y, "NET À PAYER")
    c.drawRightString(w - 4 * mm, y, "STATUT")
    y -= 4 * mm
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.05, 0.05, 0.05)
    c.drawString(4 * mm, y, format_fc(ticket.price))
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(w - 4 * mm, y + 1 * mm, ticket.statut.upper())
    y -= 6 * mm

    printed_at = ticket.created_at or datetime.now()
    emission_str = f"{printed_at.day:02d}/{printed_at.month:02d}/{printed_at.year} à {printed_at.strftime('%H:%M')}"
    cashier_name = ticket.cashier.username if ticket.cashier else "Système"
    
    row2("ÉMIS LE", emission_str, "CAISSIER", cashier_name, val_font="Helvetica", val_size=7)

    # 7. QR CODE
    y -= 2 * mm
    qr = _qr_image(ticket.qr_payload)
    qr_size = 30 * mm
    c.drawImage(qr, (w - qr_size) / 2, y - qr_size, qr_size, qr_size, mask="auto")
    y -= qr_size + 4 * mm

    # 8. FOOTER
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(w / 2, y, "*** BON VOYAGE ***")
    y -= 5 * mm
    
    c.setFont("Helvetica", 6.5)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawCentredString(w / 2, y, "Billet personnel, non remboursable 2h avant le départ.")
    y -= 3 * mm
    c.drawCentredString(w / 2, y, "Présentez-vous 30 min avant l'embarquement.")
    y -= 3 * mm
    c.drawCentredString(w / 2, y, "Les bagages en soute nécessitent un ticket séparé.")
    y -= 6 * mm
    
    # Bottom cut line
    draw_dashed_line(y)

    c.showPage()
    c.save()
    return out


def print_pdf_direct(pdf_path: Path) -> bool:
    """Print PDF directly to default physical printer without dialogs or external viewer popups.
    Returns True if sent to a physical printer, False if no physical printer is available.
    """
    try:
        from PySide6.QtPrintSupport import QPrinterInfo, QPrinter
        from PySide6.QtPdf import QPdfDocument
        from PySide6.QtGui import QPainter
        from PySide6.QtCore import QSize, QRectF

        default_info = QPrinterInfo.defaultPrinter()
        if default_info.isNull():
            return False

        printer_name = default_info.printerName()
        name_lower = printer_name.lower()
        if any(v in name_lower for v in ["pdf", "onenote", "xps", "fax", "writer", "virtual"]):
            return False

        printer = QPrinter(default_info, QPrinter.PrinterMode.HighResolution)
        printer.setDocName(pdf_path.stem)
        printer.setFullPage(True)

        doc = QPdfDocument()
        doc.load(str(pdf_path))
        if doc.pageCount() == 0:
            return False

        painter = QPainter()
        if not painter.begin(printer):
            return False

        page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
        target_w = page_rect.width()
        target_h = page_rect.height()

        for page_idx in range(doc.pageCount()):
            if page_idx > 0:
                printer.newPage()
            page_size = doc.pagePointSize(page_idx)
            dpi_scale = printer.resolution() / 72.0
            render_w = int(page_size.width() * dpi_scale)
            render_h = int(page_size.height() * dpi_scale)

            img = doc.render(page_idx, QSize(render_w, render_h))
            if not img.isNull():
                draw_w = target_w
                draw_h = target_w * (render_h / render_w)
                painter.drawImage(QRectF(0, 0, draw_w, draw_h), img)

        painter.end()
        logger.info("Direct print successful on printer: %s", printer_name)
        return True
    except Exception as e:
        logger.warning("Direct QPrinter printing failed: %s", e)
        return False


def print_ticket_windows(ticket) -> Path:
    """Generate PDF and print directly to physical printer if available, else open PDF."""
    pdf_path = generate_ticket_pdf(ticket)
    printed = False
    try:
        printed = print_pdf_direct(pdf_path)
    except Exception as e:
        logger.warning("print_ticket_windows error: %s", e)
        printed = False

    if not printed:
        # No physical printer connected -> open PDF file for the user
        try:
            import os
            os.startfile(str(pdf_path))
        except Exception:
            pass
    return pdf_path
