"""In-memory session for the logged-in cashier."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.user import User


@dataclass
class AppSession:
    user: "User | None" = None

    @property
    def is_authenticated(self) -> bool:
        return self.user is not None

    def clear(self) -> None:
        self.user = None


current_session = AppSession()
