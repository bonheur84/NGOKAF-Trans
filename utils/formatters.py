"""Format helpers."""
from __future__ import annotations

from decimal import Decimal


def format_fc(amount: Decimal | float | int | None) -> str:
    if amount is None:
        return "0 FC"
    value = int(Decimal(amount))
    return f"{value:,} FC".replace(",", " ")


# Alias historique — devise unique FC
format_fcfa = format_fc


MONTHS_FR = [
    "",
    "JAN",
    "FÉV",
    "MAR",
    "AVR",
    "MAI",
    "JUN",
    "JUL",
    "AOÛ",
    "SEP",
    "OCT",
    "NOV",
    "DÉC",
]

DAYS_FR = [
    "lundi",
    "mardi",
    "mercredi",
    "jeudi",
    "vendredi",
    "samedi",
    "dimanche",
]

MONTHS_LONG_FR = [
    "",
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
]


def format_ticket_datetime(dt) -> str:
    return f"{dt.day:02d} {MONTHS_FR[dt.month]} {dt.year} | {dt.strftime('%H:%M')}"


def format_long_date(dt) -> str:
    return (
        f"{DAYS_FR[dt.weekday()]} {dt.day} {MONTHS_LONG_FR[dt.month]} {dt.year} "
        f"- {dt.strftime('%H:%M:%S')}"
    )
