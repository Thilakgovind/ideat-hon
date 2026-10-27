"""Guardrails shared by every agent.

1. Strip phone numbers, emails and names before any LLM call.
2. The LLM never invents buses, places or fares: every option shown must be
   traceable to the data files (verify_options / grounded place names).
3. Confirm before paying or messaging anyone. SOS skips confirmation.
4. Location is used only during an active trip or SOS.
5. Logs are anonymous: area, hour, mode, intent, language. No text, phone or name.
6. Never claim an alert was sent unless it was (see describe_delivery).
"""
import re
from collections import deque

from . import data

# ---------- 1. PII stripping ----------

PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s\-()]{7,}\d)(?!\w)")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
NAME_INTRO_RE = re.compile(
    r"\b(my name is|i am|i'm|this is|naan|en peyar)\s+([A-Z][a-zA-Z]+)", re.IGNORECASE
)


def redact(text: str, names=()) -> str:
    """Remove phone numbers, emails and known/introduced names from text."""
    if not text:
        return ""
    out = EMAIL_RE.sub("[EMAIL]", text)
    out = PHONE_RE.sub(lambda m: "[PHONE]" if sum(c.isdigit() for c in m.group()) >= 8 else m.group(), out)
    out = NAME_INTRO_RE.sub(lambda m: f"{m.group(1)} [NAME]", out)
    for name in sorted({n for n in names if n and len(n) > 1}, key=len, reverse=True):
        out = re.sub(rf"\b{re.escape(name)}\b", "[NAME]", out, flags=re.IGNORECASE)
    return out


def personal_names(user: dict) -> list:
    """Names that must never reach an LLM: the user and named contacts.
    Relation words like Amma / Akka are kept, they are not identifying."""
    names = [user.get("display_name", "")]
    for c in user.get("contacts", []):
        if c.get("relation") not in ("mother", "sister", "father", "brother"):
            names.append(c.get("label", ""))
    return [n for n in names if n]


# ---------- 2. grounding ----------

def known_route_ids() -> set:
    ids = {r["id"] for r in data.routes()}
    ids |= {l["id"] for l in data.metro()["lines"]}
    ids |= {l["id"] for l in data.trains()}
    return ids


def verify_options(options: list) -> list:
    """Drop any option with a leg that does not exist in the data files."""
    known = known_route_ids()
    ok = []
    for opt in options:
        legs = [l for l in opt.get("legs", []) if l["mode"] in ("bus", "metro", "train")]
        if all(l.get("route_id") in known for l in legs):
            ok.append(opt)
    return ok


def known_place_ids() -> set:
    return {p["id"] for p in data.places()}


# ---------- 3. confirmation ----------

CONFIRM_ACTIONS = {"pay", "message", "share_trip", "invite"}
NO_CONFIRM_ACTIONS = {"sos"}


def needs_confirmation(action: str, confirmed: bool) -> bool:
    if action in NO_CONFIRM_ACTIONS:
        return False
    return action in CONFIRM_ACTIONS and not confirmed


# ---------- 4. location ----------

def location_allowed(trip_active: bool = False, sos_active: bool = False) -> bool:
    return bool(trip_active or sos_active)


def filter_location(payload: dict, allowed: bool) -> dict:
    """Return payload with lat/lng removed unless location use is allowed."""
    if allowed:
        return payload
    return {k: v for k, v in payload.items() if k not in ("lat", "lng", "location")}


# ---------- 5. anonymous logs ----------

LOG_FIELDS = {"intent", "from_area", "to_area", "hour", "mode", "lang", "channel", "route_found", "safe_place_found"}
REQUEST_LOG: deque = deque(maxlen=2000)


def anonymous_log(entry: dict) -> dict:
    clean = {k: v for k, v in entry.items() if k in LOG_FIELDS}
    for k in ("from_area", "to_area"):
        if clean.get(k) and not any(a["name"] == clean[k] for a in data.areas()):
            clean[k] = "other"  # only known areas, never free text
    REQUEST_LOG.append(clean)
    from . import store  # late import: store imports data, which this module also uses
    row = {**clean, "area": clean.get("to_area") or clean.get("from_area"), "source": "live"}
    row = {k: v for k, v in row.items() if k in ("area", "hour", "mode", "lang", "channel", "intent", "route_found",
                                                   "safe_place_found", "source")}
    if row.get("channel") not in ("app", "sms", "voice", "call"):
        row["channel"] = "app"
    store.persist("request_log", row, method="insert")
    return clean


# ---------- 6. honest delivery ----------

def describe_delivery(results: list) -> dict:
    """Summarise send results without overstating what happened."""
    sent = [r for r in results if r.get("status") == "sent"]
    mock = [r for r in results if r.get("status") == "mock_logged"]
    return {
        "sent": len(sent),
        "demo_logged": len(mock),
        "not_sent": len(results) - len(sent) - len(mock),
        "any_real_alert": bool(sent),
    }


# ---------- SMS size ----------

def clamp_sms(text: str, tamil: bool = False) -> str:
    limit = 70 if tamil else 160
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."
