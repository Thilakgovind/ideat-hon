"""SMS agent: Twilio send/receive. Mock (logged, not sent) when keys are missing."""
import xml.sax.saxutils as sax
from collections import deque
from datetime import datetime

import httpx

from .. import config
from ..guardrails import clamp_sms

OUTBOX: deque = deque(maxlen=200)  # demo log; phone numbers are masked
TWILIO_URL = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"


def mask(phone):
    if not phone:
        return None
    digits = [c for c in phone if c.isdigit()]
    return "•••• " + "".join(digits[-2:]) if len(digits) >= 4 else "••••"


def is_tamil(text: str) -> bool:
    return any("஀" <= ch <= "௿" for ch in text or "")


def send(to: str, body: str, purpose: str = "message") -> dict:
    """Send one SMS. Returns status: sent | mock_logged | no_phone | failed."""
    body = clamp_sms(body, tamil=is_tamil(body))
    entry = {"to": mask(to), "body": body, "purpose": purpose, "at": datetime.utcnow().isoformat() + "Z"}
    if not config.has("twilio"):
        entry["status"] = "mock_logged"
    elif not to:
        entry["status"] = "no_phone"
    else:
        try:
            r = httpx.post(
                TWILIO_URL.format(sid=config.env("TWILIO_ACCOUNT_SID")),
                data={"To": to, "From": config.env("TWILIO_PHONE_NUMBER"), "Body": body},
                auth=(config.env("TWILIO_ACCOUNT_SID"), config.env("TWILIO_AUTH_TOKEN")),
                timeout=10,
            )
            entry["status"] = "sent" if r.status_code in (200, 201) else "failed"
            if entry["status"] == "sent":
                entry["sid"] = r.json().get("sid")
            else:
                entry["error"] = f"twilio_http_{r.status_code}"
        except httpx.HTTPError as e:
            entry["status"] = "failed"
            entry["error"] = type(e).__name__
    entry["provider"] = "twilio" if config.has("twilio") else "mock"
    OUTBOX.append(entry)
    return entry


def parse_inbound(form: dict) -> dict:
    """Twilio inbound webhook form -> {from, body}."""
    return {"from": (form.get("From") or "").strip(), "body": (form.get("Body") or "").strip()}


def twiml(message: str) -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{sax.escape(message)}</Message></Response>'
