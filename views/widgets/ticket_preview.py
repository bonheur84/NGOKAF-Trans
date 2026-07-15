"""Ticket preview widget — live thermal slip look."""
from __future__ import annotations

import io
from datetime import datetime

import qrcode
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout

from config.settings import settings
from resources import theme as T
from utils.formatters import MONTHS_FR, format_fc


class TicketPreview(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ticketPreview")
        self.setStyleSheet(
            f"""
            QFrame#ticketPreview {{
                background: {T.BG_CARD};
                border: 2px dashed {T.BORDER};
                border-radius: 12px;
            }}
            """
        )
        self.setMinimumWidth(220)
        self.setMaximumWidth(260)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = settings.logo_path
        if logo_path.exists():
            pix = QPixmap(str(logo_path)).scaled(
                70, 55, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self.logo.setPixmap(pix)
        lay.addWidget(self.logo)

        self.agency = QLabel(settings.AGENCY_NAME)
        self.agency.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.agency.setStyleSheet(f"font-size:13px; font-weight:700; color:{T.TEXT_PRIMARY};")
        lay.addWidget(self.agency)

        self.phone = QLabel(settings.AGENCY_PHONE)
        self.phone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.phone.setStyleSheet(f"font-size:11px; color:{T.TEXT_SECONDARY};")
        lay.addWidget(self.phone)

        self.address = QLabel(settings.AGENCY_ADDRESS)
        self.address.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.address.setStyleSheet(f"font-size:11px; color:{T.TEXT_SECONDARY};")
        lay.addWidget(self.address)

        self.numero = QLabel("BILLET N°: —")
        self.numero.setStyleSheet(f"font-size:12px; font-weight:600; color:{T.TEXT_PRIMARY}; margin-top:8px;")
        lay.addWidget(self.numero)

        self.date_lbl = QLabel("DATE: —")
        self.date_lbl.setStyleSheet(f"font-size:12px; color:{T.TEXT_PRIMARY};")
        lay.addWidget(self.date_lbl)

        self.passenger = QLabel("PASSAGER")
        self.passenger.setStyleSheet(f"font-size:13px; font-weight:700; color:{T.TEXT_PRIMARY}; margin-top:6px;")
        lay.addWidget(self.passenger)

        self.tel = QLabel("")
        self.tel.setStyleSheet(f"font-size:12px; color:{T.TEXT_SECONDARY};")
        lay.addWidget(self.tel)

        self.trajet = QLabel("TRAJET: —")
        self.trajet.setStyleSheet(f"font-size:12px; color:{T.TEXT_PRIMARY}; margin-top:6px;")
        lay.addWidget(self.trajet)

        self.siege = QLabel("SIÈGE: —")
        self.siege.setStyleSheet(f"font-size:12px; color:{T.TEXT_PRIMARY};")
        lay.addWidget(self.siege)

        self.total = QLabel("NET À PAYER : —")
        self.total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total.setStyleSheet(
            f"font-size:14px; font-weight:800; color:{T.TEXT_PRIMARY}; margin-top:10px;"
        )
        lay.addWidget(self.total)

        self.qr = QLabel()
        self.qr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr.setFixedSize(100, 100)
        lay.addWidget(self.qr, alignment=Qt.AlignmentFlag.AlignCenter)

        footer = QLabel("Bon voyage avec Ngokaf !\nGardez ce ticket précieusement.")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(f"font-size:11px; color:{T.TEXT_SECONDARY};")
        lay.addWidget(footer)
        lay.addStretch()

    def update_preview(
        self,
        *,
        numero: str = "—",
        passenger: str = "PASSAGER",
        phone: str = "",
        route: str = "—",
        seat: str = "—",
        price: str = "—",
        when: datetime | None = None,
        qr_text: str = "",
    ) -> None:
        self.numero.setText(f"BILLET N°: {numero}")
        if when:
            d = f"{when.day:02d} {MONTHS_FR[when.month]} {when.year} | {when.strftime('%H:%M')}"
            self.date_lbl.setText(f"DATE: {d}")
        else:
            self.date_lbl.setText("DATE: —")
        self.passenger.setText(passenger or "PASSAGER")
        self.tel.setText(phone or "")
        self.trajet.setText(f"TRAJET: {route}")
        self.siege.setText(f"SIÈGE: {seat}")
        self.total.setText(f"NET À PAYER : {price}")
        payload = qr_text or f"{numero}|{passenger}|{phone}|{route}|{seat}|{price}"
        img = qrcode.make(payload, border=1)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qimg = QImage.fromData(buf.getvalue())
        self.qr.setPixmap(
            QPixmap.fromImage(qimg).scaled(
                96, 96, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
        )
