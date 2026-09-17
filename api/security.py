"""Small, dependency-free signed session tokens for the central API."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time


def _secret() -> bytes:
    value = os.environ.get("API_TOKEN_SECRET", "")
    if len(value) < 32:
        raise RuntimeError("API_TOKEN_SECRET doit contenir au moins 32 caractères.")
    return value.encode("utf-8")


def issue_token(user_id: int, agency_id: int | None, role: str, ttl_seconds: int = 28800) -> str:
    payload = {
        "sub": user_id,
        "agency_id": agency_id,
        "role": role,
        "exp": int(time.time()) + ttl_seconds,
    }
    raw = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).rstrip(b"=")
    signature = hmac.new(_secret(), raw, hashlib.sha256).digest()
    return f"{raw.decode()}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"


def verify_token(token: str) -> dict:
    try:
        raw_b64, signature_b64 = token.split(".", 1)
        raw = raw_b64.encode()
        expected = hmac.new(_secret(), raw, hashlib.sha256).digest()
        supplied = base64.urlsafe_b64decode(signature_b64 + "=" * (-len(signature_b64) % 4))
        if not hmac.compare_digest(expected, supplied):
            raise ValueError("signature invalide")
        payload = json.loads(base64.urlsafe_b64decode(raw_b64 + "=" * (-len(raw_b64) % 4)))
        if int(payload["exp"]) < time.time():
            raise ValueError("session expirée")
        return payload
    except Exception as exc:
        raise ValueError("jeton invalide") from exc
