"""Sales controller."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from database.session import get_session
from services.sale_service import sell_ticket, cancel_ticket, search_tickets, occupied_seats
from services.bus_service import list_active_routes
from services.print_service import print_ticket


class VentesController:
    def list_routes(self):
        session = get_session()
        try:
            return list_active_routes(session)
        finally:
            session.close()

    def get_occupied(self, bus_id: int, route_id: int, travel_date: date):
        session = get_session()
        try:
            return occupied_seats(session, bus_id, route_id, travel_date)
        finally:
            session.close()

    def sell(self, **kwargs):
        session = get_session()
        try:
            return sell_ticket(session, **kwargs)
        finally:
            session.close()

    def cancel(self, ticket_id: int, cashier, reason: str | None = None):
        session = get_session()
        try:
            return cancel_ticket(session, ticket_id, cashier, reason)
        finally:
            session.close()

    def search(self, **kwargs):
        session = get_session()
        try:
            return search_tickets(session, **kwargs)
        finally:
            session.close()

    def print_ticket(self, ticket, user_id=None, preview_only=False):
        return print_ticket(ticket, user_id, preview_only)
