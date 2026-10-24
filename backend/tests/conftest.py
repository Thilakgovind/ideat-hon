import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend import config, data, orchestrator  # noqa: E402
from backend.agents import circle, pay, sms  # noqa: E402


@pytest.fixture(autouse=True)
def mock_mode_and_clean_state(monkeypatch):
    """Every test starts in full mock mode (no real API calls) with fresh in-memory state."""
    for keys in config.SERVICE_KEYS.values():
        for k in keys:
            monkeypatch.setenv(k, "")
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
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload
