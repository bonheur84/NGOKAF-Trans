"""Central HTTPS API: the only component allowed to access MySQL in production."""
from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import text

from database.connection import get_engine
from database.init_db import init_database
from database.session import get_session
from models.luggage import Luggage
from models.user import User
from services import auth_service
from services.agency_service import get_agency
from services import bus_service, luggage_service, sale_service
from services.audit_service import log_audit
from api.security import issue_token, verify_token


@asynccontextmanager
async def lifespan(_: FastAPI):
    # The server owns schema initialization; desktop clients never see MySQL.
    init_database()
    yield


app = FastAPI(title="NGOKAF TRANS API", version="1.0.0", lifespan=lifespan)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class TicketSaleRequest(BaseModel):
    passenger_name: str = Field(min_length=1, max_length=150)
    phone: str = Field(min_length=1, max_length=30)
    route_id: int = Field(gt=0)
    seat_number: int = Field(gt=0)
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    travel_date: date


class TicketCancellationRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=255)


class LuggageRegistrationRequest(BaseModel):
    sender_name: str = Field(min_length=1, max_length=150)
    sender_phone: str = Field(min_length=1, max_length=30)
    recipient_name: str = Field(min_length=1, max_length=150)
    recipient_phone: str = Field(min_length=1, max_length=30)
    description: str = Field(min_length=1)
    poids: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    valeur_declaree: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    route_id: int = Field(gt=0)
    luggage_code: str = Field(min_length=1, max_length=30)
    fragile: bool = False


class LuggageStatusRequest(BaseModel):
    statut: str = Field(pattern="^(enregistre|charge|livre|annule)$")


def user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "nom": user.nom,
        "prenom": user.prenom,
        "role": user.role,
        "agency_id": user.agency_id,
    }


def ticket_payload(ticket) -> dict:
    return {
        "id": ticket.id,
        "numero": ticket.numero,
        "luggage_code": ticket.luggage_code,
        "passenger_name": ticket.passenger_name,
        "phone": ticket.phone,
        "route_id": ticket.route_id,
        "bus_id": ticket.bus_id,
        "seat_number": ticket.seat_number,
        "price": str(ticket.price),
        "travel_date": ticket.travel_date.isoformat(),
        "statut": ticket.statut,
        "qr_payload": ticket.qr_payload,
        "created_at": ticket.created_at.isoformat(),
    }


def luggage_payload(item) -> dict:
    return {
        "id": item.id,
        "numero": item.numero,
        "ticket_numero": item.ticket_numero,
        "route_id": item.route_id,
        "bus_id": item.bus_id,
        "route_label": item.route_label,
        "bus_code": item.bus_code,
        "sender_name": item.sender_name,
        "sender_phone": item.sender_phone,
        "recipient_name": item.recipient_name,
        "recipient_phone": item.recipient_phone,
        "description": item.description,
        "poids": str(item.poids),
        "valeur_declaree": str(item.valeur_declaree) if item.valeur_declaree is not None else None,
        "total": str(item.total),
        "statut": item.statut,
        "fragile": item.fragile,
        "barcode": item.barcode,
        "qr_payload": item.qr_payload,
        "created_at": item.created_at.isoformat(),
    }


def current_user(request: Request) -> User:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session requise")
    try:
        claims = verify_token(header[7:])
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalide")
    session = get_session()
    try:
        user = session.get(User, claims["sub"])
        if not user or user.statut != "actif":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Compte indisponible")
        session.expunge(user)
        return user
    finally:
        session.close()


@app.get("/health")
def health() -> dict:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Base de données indisponible") from exc
    return {"status": "ok"}


@app.post("/v1/auth/login")
def login(body: LoginRequest) -> dict:
    session = get_session()
    try:
        user = auth_service.authenticate(session, body.username, body.password)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants incorrects")
        agency = get_agency(session, user.agency_id) if user.agency_id else None
        return {
            "access_token": issue_token(user.id, user.agency_id, user.role),
            "token_type": "bearer",
            "user": user_payload(user),
            "agency": {"id": agency.id, "name": agency.name, "code": agency.code} if agency else None,
        }
    finally:
        session.close()


@app.get("/v1/session")
def session_info(user: User = Depends(current_user)) -> dict:
    return {"user": user_payload(user)}


@app.get("/v1/routes")
def routes(user: User = Depends(current_user)) -> list[dict]:
    session = get_session()
    try:
        items = bus_service.list_active_routes(session, agency_id=user.agency_id)
        return [
            {
                "id": route.id,
                "departure": route.ville_depart,
                "arrival": route.ville_arrivee,
                "departure_time": route.heure_depart.strftime("%H:%M"),
                "price": str(route.prix_indicatif) if route.prix_indicatif is not None else None,
                "bus": {"id": route.bus.id, "code": route.bus.code, "capacity": route.bus.capacite},
            }
            for route in items
        ]
    finally:
        session.close()


@app.get("/v1/routes/{route_id}/occupied-seats")
def route_occupied_seats(
    route_id: int,
    travel_date: date,
    user: User = Depends(current_user),
) -> dict:
    session = get_session()
    try:
        route = bus_service.get_route(session, route_id, agency_id=user.agency_id)
        if not route:
            raise HTTPException(status_code=404, detail="Trajet introuvable")
        return {"route_id": route.id, "travel_date": travel_date.isoformat(), "occupied_seats": sorted(sale_service.occupied_seats(session, route.bus_id, route.id, travel_date))}
    finally:
        session.close()


@app.post("/v1/tickets", status_code=status.HTTP_201_CREATED)
def create_ticket(body: TicketSaleRequest, user: User = Depends(current_user)) -> dict:
    session = get_session()
    try:
        ticket = sale_service.sell_ticket(session, cashier=user, **body.model_dump())
        return ticket_payload(ticket)
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        session.close()


@app.get("/v1/tickets")
def tickets(
    query: str = "",
    limit: int = Query(default=100, ge=1, le=200),
    user: User = Depends(current_user),
) -> list[dict]:
    session = get_session()
    try:
        return [ticket_payload(ticket) for ticket in sale_service.search_tickets(session, query=query, limit=limit, agency_id=user.agency_id)]
    finally:
        session.close()


@app.post("/v1/tickets/{ticket_id}/cancel")
def cancel_ticket(ticket_id: int, body: TicketCancellationRequest, user: User = Depends(current_user)) -> dict:
    session = get_session()
    try:
        return ticket_payload(sale_service.cancel_ticket(session, ticket_id, user, body.reason))
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        session.close()


@app.get("/v1/luggage/ticket/{luggage_code}")
def luggage_ticket(luggage_code: str, user: User = Depends(current_user)) -> dict:
    session = get_session()
    try:
        ticket = luggage_service.find_ticket_for_luggage(session, luggage_code, agency_id=user.agency_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Billet introuvable ou invalide")
        return ticket_payload(ticket)
    finally:
        session.close()


@app.post("/v1/luggage", status_code=status.HTTP_201_CREATED)
def create_luggage(body: LuggageRegistrationRequest, user: User = Depends(current_user)) -> dict:
    session = get_session()
    try:
        payload = body.model_dump(exclude={"luggage_code"})
        ticket = luggage_service.find_ticket_for_luggage(session, body.luggage_code, agency_id=user.agency_id)
        item = luggage_service.register_luggage(
            session, cashier=user, ticket=ticket, frais_base=None, supplement_poids=None, total=None, **payload
        )
        return luggage_payload(item)
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        session.close()


@app.get("/v1/luggage")
def luggage(
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(current_user),
) -> list[dict]:
    session = get_session()
    try:
        return [luggage_payload(item) for item in luggage_service.list_recent_luggage(session, limit=limit, agency_id=user.agency_id)]
    finally:
        session.close()


@app.patch("/v1/luggage/{luggage_id}/status")
def update_luggage_status(luggage_id: int, body: LuggageStatusRequest, user: User = Depends(current_user)) -> dict:
    session = get_session()
    try:
        item = session.get(Luggage, luggage_id)
        if not item or item.agency_id != user.agency_id:
            raise HTTPException(status_code=404, detail="Bagage introuvable")
        item.statut = body.statut
        log_audit(session, "status", "luggage", item.id, user.id, {"statut": body.statut})
        session.commit()
        session.refresh(item)
        return luggage_payload(item)
    finally:
        session.close()
