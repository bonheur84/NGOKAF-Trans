"""HTTPS client used by desktop installations.

Only a public API URL and a short-lived login token live on a cashier PC;
database passwords never leave the server.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from config.settings import settings


class ApiError(RuntimeError):
    """A user-facing API failure."""


@dataclass
class ApiLogin:
    token: str
    user: dict[str, Any]
    agency: dict[str, Any] | None


class ApiClient:
    def __init__(self, base_url: str | None = None, token: str | None = None):
        self.base_url = (base_url or settings.API_BASE_URL).rstrip("/")
        self.token = token
        if not self.base_url:
            raise ApiError("URL de l'API centrale non configurée.")

    def _request(self, method: str, path: str, **kwargs) -> Any:
        headers = dict(kwargs.pop("headers", {}))
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            response = httpx.request(
                method,
                f"{self.base_url}{path}",
                headers=headers,
                timeout=settings.API_TIMEOUT_SECONDS,
                **kwargs,
            )
        except httpx.RequestError as exc:
            raise ApiError("Impossible de joindre le serveur central. Vérifiez Internet.") from exc
        if response.is_success:
            return response.json() if response.content else None
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        if response.status_code == 401:
            raise ApiError("Session expirée ou identifiants incorrects.")
        raise ApiError(str(detail or f"Erreur serveur ({response.status_code})"))

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def login(self, username: str, password: str) -> ApiLogin:
        data = self._request("POST", "/v1/auth/login", json={"username": username, "password": password})
        return ApiLogin(data["access_token"], data["user"], data.get("agency"))

    def routes(self) -> list[dict[str, Any]]:
        return self._request("GET", "/v1/routes")

    def occupied_seats(self, route_id: int, travel_date: str) -> set[int]:
        data = self._request("GET", f"/v1/routes/{route_id}/occupied-seats", params={"travel_date": travel_date})
        return set(data["occupied_seats"])

    def create_ticket(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/tickets", json=payload)

    def tickets(self, query: str = "", limit: int = 200) -> list[dict[str, Any]]:
        return self._request("GET", "/v1/tickets", params={"query": query, "limit": limit})

    def cancel_ticket(self, ticket_id: int, reason: str | None = None) -> dict[str, Any]:
        return self._request("POST", f"/v1/tickets/{ticket_id}/cancel", json={"reason": reason})

    def ticket_for_luggage(self, code: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/luggage/ticket/{code}")

    def create_luggage(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/luggage", json=payload)

    def luggage(self, limit: int = 200) -> list[dict[str, Any]]:
        return self._request("GET", "/v1/luggage", params={"limit": limit})

    def update_luggage_status(self, luggage_id: int, statut: str) -> dict[str, Any]:
        return self._request("PATCH", f"/v1/luggage/{luggage_id}/status", json={"statut": statut})


def current_api_client() -> ApiClient:
    from services.session_store import current_session

    return ApiClient(token=current_session.access_token)
