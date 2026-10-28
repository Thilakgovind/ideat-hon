"""Supabase Auth on the backend: turn a login token into a private user id.

The browser signs in with Supabase phone OTP and sends `Authorization: Bearer <token>`.
We ask Supabase who that token belongs to (GET /auth/v1/user) and map the auth id to
`u_<hash>`, so the phone number is never used as an id and never logged.
No token (or Supabase not configured) -> the demo user. Invalid token -> 401.
"""
import hashlib
import threading
import time

import httpx

from . import config

DEMO_USER = "u_demo"
CACHE_SECONDS = 300
_cache: dict = {}
_lock = threading.Lock()


def enabled() -> bool:
    return config.has("supabase_public")


def user_id_for(auth_id: str) -> str:
    return "u_" + hashlib.sha256(f"supabase:{auth_id}".encode()).hexdigest()[:16]


def mask_phone(phone) -> str:
    digits = "".join(c for c in (phone or "") if c.isdigit())
    return ("+" + digits[:2] + " ••••• •" + digits[-4:]) if len(digits) >= 10 else ""


class AuthError(Exception):
    pass


def verify(token: str) -> dict:
    """Return {user_id, auth_id, phone} for a valid Supabase access token, else raise AuthError."""
    key = hashlib.sha256(token.encode()).hexdigest()
    now = time.time()
    with _lock:
        hit = _cache.get(key)
        if hit and hit[0] > now:
            return hit[1]
    if not enabled():
        raise AuthError("auth_not_configured")
    try:
        r = httpx.get(config.env("SUPABASE_URL").rstrip("/") + "/auth/v1/user",
                      headers={"apikey": config.env("SUPABASE_ANON_KEY"), "Authorization": f"Bearer {token}"}, timeout=10)
    except httpx.HTTPError as e:
        raise AuthError("auth_unreachable") from e
    if r.status_code != 200:
        raise AuthError("invalid_token")
    u = r.json()
    who = {"user_id": user_id_for(u["id"]), "auth_id": u["id"], "phone": u.get("phone") or None}
    with _lock:
        _cache[key] = (now + CACHE_SECONDS, who)
    return who


def from_header(authorization) -> dict | None:
    """None when there is no bearer token (demo user). Raises AuthError on a bad token."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return verify(authorization.split(" ", 1)[1].strip())
