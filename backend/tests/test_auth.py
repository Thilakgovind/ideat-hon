"""Supabase sign-in on the backend: token -> private user id; phone masked; demo user without a token."""
from fastapi.testclient import TestClient

from backend import auth
from backend.app import app

c = TestClient(app)
PHONE = "+919876543210"


def _fake_verify(monkeypatch, valid="good-token"):
    def verify(token):
        if token != valid:
            raise auth.AuthError("invalid_token")
        return {"user_id": auth.user_id_for("auth-123"), "auth_id": "auth-123", "phone": PHONE}
    monkeypatch.setattr(auth, "verify", verify)


def test_no_token_is_demo_user():
    r = c.get("/api/me").json()
    assert r["user_id"] == "u_demo" and r["signed_in"] is False and r["phone_masked"] is None


def test_bad_token_is_refused(monkeypatch):
    _fake_verify(monkeypatch)
    r = c.get("/api/me", headers={"Authorization": "Bearer nope"})
    assert r.status_code == 401


def test_signed_in_user_gets_hashed_id_and_masked_phone(monkeypatch):
    _fake_verify(monkeypatch)
    r = c.get("/api/me", headers={"Authorization": "Bearer good-token"}).json()
    assert r["signed_in"] and r["user_id"].startswith("u_") and r["user_id"] != "u_demo"
    assert "9876543210" not in str(r) and r["phone_masked"].endswith("3210")
    assert r["needs_setup"] is True


def test_profile_setup_saves_and_never_returns_phone(monkeypatch):
    _fake_verify(monkeypatch)
    h = {"Authorization": "Bearer good-token"}
    r = c.put("/api/me", json={"display_name": "Meena", "start_area": "Kilpauk", "lang": "ta"}, headers=h).json()
    assert r["display_name"] == "Meena" and r["needs_setup"] is False and PHONE not in str(r)
    assert c.get("/api/profile", headers=h).json()["display_name"] == "Meena"


def test_saving_profile_needs_sign_in():
    assert c.put("/api/me", json={"display_name": "X"}).status_code == 401


def test_circle_is_per_user(monkeypatch):
    _fake_verify(monkeypatch)
    mine = c.get("/api/circle", headers={"Authorization": "Bearer good-token"}).json()
    demo = c.get("/api/circle").json()
    assert len(mine.get("contacts", [])) == 0 and len(demo.get("contacts", [])) > 0


def test_mask_phone():
    assert auth.mask_phone(PHONE) == "+91 ••••• •3210"
    assert auth.mask_phone(None) == "" and auth.mask_phone("123") == ""
