import sys
from datetime import datetime
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend import config, data, orchestrator, store  # noqa: E402
from backend.agents import circle, pay, sms  # noqa: E402


@pytest.fixture(autouse=True)
def mock_mode_and_clean_state(monkeypatch):
    """Every test starts in full mock mode (no real API calls) with fresh in-memory state."""
    for keys in config.SERVICE_KEYS.values():
        for k in keys:
            monkeypatch.setenv(k, "")
    for k in ("SMS_PROVIDER", "PUBLIC_BACKEND_URL", "TEXTBEE_WEBHOOK_SECRET", "N8N_ORCHESTRATOR_URL", "SUPABASE_DB_URL"):
        monkeypatch.setenv(k, "")
    data.reset()
    store.STATUS.update(mode="memory", checked_at=0, loaded={})
    circle.STORE.reset()
    orchestrator.SESSIONS.clear()
    sms.OUTBOX.clear()
    pay.ORDERS.clear()
    pay.TICKETS.clear()
    yield


def at(hhmm: str) -> datetime:
    h, m = map(int, hhmm.split(":"))
    return datetime(2026, 10, 24, h, m, tzinfo=data.IST)


class FakeResponse:
    def __init__(self, status_code=200, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.headers = headers or {"content-type": "application/json"}
        self.content = b""

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(f"HTTP {self.status_code}", request=None, response=None)
