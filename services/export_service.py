"""Export helpers — PDF, Excel, CSV."""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def export_tickets_csv(tickets, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(
            [
                "Numero",
                "Date",
                "Passager",
                "Telephone",
                "Trajet",
                "Bus",
                "Siege",
                "Prix",
                "Caissier",
                "Statut",
            ]
        )
        for t in tickets:
            w.writerow(
                [
                    t.numero,
                    t.date_vente.isoformat(),
                    t.passenger_name,
                    t.phone,
                    t.route.short_label if t.route else "",
                    t.bus.code if t.bus else "",
                    t.seat_number,
                    float(t.price),
                    t.cashier.full_name if t.cashier else "",
                    t.statut,
                ]
            )
    return path


def export_tickets_excel(tickets, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Ventes"
    ws.append(
        [
            "Numero",
            "Date",
            "Passager",
            "Telephone",
            "Trajet",
            "Bus",
            "Siege",
            "Prix",
            "Caissier",
            "Statut",
        ]
    )
    for t in tickets:
        ws.append(
            [
                t.numero,
                t.date_vente.isoformat(),
                t.passenger_name,
                t.phone,
                t.route.short_label if t.route else "",
                t.bus.code if t.bus else "",
                t.seat_number,
                float(t.price),
                t.cashier.full_name if t.cashier else "",
                t.statut,
            ]
        )
    wb.save(path)
    return path


def export_tickets_pdf(tickets, path: Path, title: str = "Historique des ventes") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    y = height - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, title)
    y -= 20
    c.setFont("Helvetica", 9)
    c.drawString(40, y, f"Exporté le {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    y -= 24
    headers = "Numéro | Date | Passager | Tél | Trajet | Siège | Prix | Statut"
    c.setFont("Helvetica-Bold", 8)
    c.drawString(40, y, headers)
    y -= 14
    c.setFont("Helvetica", 8)
    for t in tickets:
        line = (
            f"{t.numero} | {t.date_vente} | {t.passenger_name[:20]} | {t.phone} | "
            f"{(t.route.short_label if t.route else '')[:22]} | {t.seat_number} | "
            f"{float(t.price):.0f} | {t.statut}"
        )
        if y < 40:
            c.showPage()
            y = height - 40
            c.setFont("Helvetica", 8)
        c.drawString(40, y, line[:120])
        y -= 12
    c.save()
    return path


def export_luggage_csv(items, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(
            [
                "Numero",
                "Expediteur",
                "Destinataire",
                "Description",
                "Poids",
                "Total",
                "Bus",
                "Trajet",
                "Statut",
                "Date",
            ]
        )
        for i in items:
            w.writerow(
                [
                    i.numero,
                    i.sender_name,
                    i.recipient_name,
                    i.description,
                    float(i.poids),
                    float(i.total),
                    i.bus.code if i.bus else "",
                    i.route.short_label if i.route else "",
                    i.statut,
                    i.created_at.isoformat(sep=" ", timespec="minutes"),
                ]
            )
    return path


def export_luggage_excel(items, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Bagages"
    ws.append(
        [
            "Numero",
            "Expediteur",
            "Destinataire",
            "Description",
            "Poids",
            "Total",
            "Bus",
            "Trajet",
            "Statut",
            "Date",
        ]
    )
    for i in items:
        ws.append(
            [
                i.numero,
                i.sender_name,
                i.recipient_name,
                i.description,
                float(i.poids),
                float(i.total),
                i.bus.code if i.bus else "",
                i.route.short_label if i.route else "",
                i.statut,
                i.created_at.isoformat(sep=" ", timespec="minutes"),
            ]
        )
    wb.save(path)
    return path


def export_luggage_pdf(items, path: Path, title: str = "Manifeste bagages") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    y = height - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, title)
    y -= 24
    c.setFont("Helvetica", 8)
    for i in items:
        line = (
            f"{i.numero} | {i.sender_name[:18]} | {i.recipient_name[:18]} | "
            f"{float(i.poids)}kg | {i.statut} | {float(i.total):.0f} FC"
        )
        if y < 40:
            c.showPage()
            y = height - 40
            c.setFont("Helvetica", 8)
        c.drawString(40, y, line[:120])
        y -= 12
    c.save()
    return path
