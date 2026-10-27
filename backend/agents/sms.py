"""SMS agent: one send() for every provider, picked by SMS_PROVIDER.

    textbee  = main (Android phone gateway, TEXTBEE_API_KEY + TEXTBEE_DEVICE_ID)
    twilio   = TWILIO_PHONE_NUMBER (trial accounts: verified numbers only)
    fast2sms = outbound only (FAST2SMS_API_KEY)
    mock     = demo outbox only

Statuses are honest: "sent" only when the provider accepted the message.
Anything else is "not_sent" (with a reason) or "mock_logged". Every attempt is
kept in OUTBOX with the phone masked, so /api/demo/outbox can show what happened.
"""
import base64
import hashlib
import hmac
import re
import xml.sax.saxutils as sax
from collections import deque
from datetime import datetime

import httpx

from .. import config
from ..guardrails import clamp_sms

OUTBOX: deque = deque(maxlen=200)
TWILIO_URL = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
TEXTBEE_SEND = "https://api.textbee.dev/api/v1/gateway/devices/{device}/send-sms"
FAST2SMS_URL = "https://www.fast2sms.com/dev/bulkV2"
FAKE_NUMBER = re.compile(r"^\+?91\s?0{5}")  # sample numbers like +91 00000 00011 are never real
TIMEOUT = 15


def mask(phone):
    if not phone:
        return None
    digits = [c for c in phone if c.isdigit()]
    return "•••• " + "".join(digits[-2:]) if len(digits) >= 4 else "••••"


def is_tamil(text: str) -> bool:
    return any("஀" <= ch <= "௿" for ch in text or "")


def _e164(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 10:
        digits = "91" + digits
    return "+" + digits if digits else ""


# ---------------------------------------------------------------- providers

def _twilio(to, body):
    r = httpx.post(TWILIO_URL.format(sid=config.env("TWILIO_ACCOUNT_SID")),
                   data={"To": to, "From": config.env("TWILIO_PHONE_NUMBER"), "Body": body},
                   auth=(config.env("TWILIO_ACCOUNT_SID"), config.env("TWILIO_AUTH_TOKEN")), timeout=TIMEOUT)
    if r.status_code in (200, 201):
        return {"status": "sent", "ref": r.json().get("sid")}
    return {"status": "not_sent", "reason": f"twilio_http_{r.status_code}"}


def _textbee(to, body):
    r = httpx.post(TEXTBEE_SEND.format(device=config.env("TEXTBEE_DEVICE_ID")),
                   headers={"x-api-key": config.env("TEXTBEE_API_KEY")},
                   json={"recipients": [to], "message": body}, timeout=TIMEOUT)
    if r.status_code in (200, 201):
        data = r.json().get("data", {}) if r.headers.get("content-type", "").startswith("application/json") else {}
        return {"status": "sent", "ref": data.get("smsBatchId") or data.get("_id")}
    return {"status": "not_sent", "reason": f"textbee_http_{r.status_code}"}


def _fast2sms(to, body):
    digits = re.sub(r"\D", "", to)[-10:]
    r = httpx.post(FAST2SMS_URL, headers={"authorization": config.env("FAST2SMS_API_KEY")},
                   json={"route": "q", "message": body, "numbers": digits, "flash": 0}, timeout=TIMEOUT)
    ok = r.status_code == 200 and r.json().get("return") is True
    return {"status": "sent", "ref": r.json().get("request_id")} if ok else {"status": "not_sent", "reason": f"fast2sms_http_{r.status_code}"}


PROVIDERS = {"twilio": _twilio, "textbee": _textbee, "fast2sms": _fast2sms}


def send(to: str, body: str, purpose: str = "message") -> dict:
    """Send one SMS with the selected provider. Never raises."""
    body = clamp_sms(body, tamil=is_tamil(body))
    provider = config.sms_provider()
    entry = {"to": mask(to), "body": body, "purpose": purpose, "provider": provider,
             "at": datetime.utcnow().isoformat() + "Z"}
    if provider == "mock":
        entry["status"] = "mock_logged"
    elif not to:
        entry.update(status="not_sent", reason="no_phone")
    elif FAKE_NUMBER.match(re.sub(r"[\s-]", "", to)):
        entry.update(status="not_sent", reason="sample_number")
    else:
        try:
            entry.update(PROVIDERS[provider](_e164(to), body))
        except (httpx.HTTPError, ValueError, KeyError) as e:
            entry.update(status="not_sent", reason=type(e).__name__)
    OUTBOX.append(entry)
    return entry


# ---------------------------------------------------------------- inbound

def parse_inbound(form: dict) -> dict:
    """Twilio inbound webhook form -> {from, body}."""
    return {"from": (form.get("From") or "").strip(), "body": (form.get("Body") or "").strip()}


def parse_textbee(payload) -> dict:
    """textbee webhook JSON -> {from, body}, or None for anything that is not an inbound SMS."""
    if not isinstance(payload, dict):
        return None
    event = str(payload.get("event") or payload.get("webhookEvent") or "").upper()
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    sender = data.get("sender") or data.get("from") or data.get("phoneNumber")
    text = data.get("message") or data.get("body") or data.get("text")
    if event and event not in ("MESSAGE_RECEIVED", "SMS_RECEIVED", "RECEIVED"):
        return None
    if not isinstance(sender, str) or not isinstance(text, str):
        return None
    sender, text = sender.strip(), text.strip()
    if not re.fullmatch(r"\+?\d[\d\s-]{6,18}", sender) or not text or len(text) > 640:
        return None
    return {"from": sender, "body": text}


def verify_textbee(raw: bytes, signature: str) -> bool:
    """HMAC-SHA256 check when TEXTBEE_WEBHOOK_SECRET is set (accepts hex or sha256=hex)."""
    secret = config.env("TEXTBEE_WEBHOOK_SECRET")
    if not secret:
        return True
    expected = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    sig = (signature or "").split("=", 1)[-1].strip()
    return hmac.compare_digest(expected, sig)


def verify_twilio(url: str, params: dict, signature: str) -> bool:
    """Twilio X-Twilio-Signature check (HMAC-SHA1 of URL + sorted params) when the auth token is set."""
    token = config.env("TWILIO_AUTH_TOKEN")
    if not token or not config.env("PUBLIC_BACKEND_URL"):
        return True  # local / demo: no public URL to sign against
    data = url + "".join(f"{k}{params[k]}" for k in sorted(params))
    expected = base64.b64encode(hmac.new(token.encode(), data.encode(), hashlib.sha1).digest()).decode()
    return hmac.compare_digest(expected, signature or "")


def twiml(message: str) -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{sax.escape(message)}</Message></Response>'
