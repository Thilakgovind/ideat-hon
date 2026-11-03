"""Authenticated athlete requests and a server-only n8n notification boundary."""
import hmac
from typing import Literal
from urllib.parse import urlparse
from uuid import UUID

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from . import auth, config, vm_repository as db

router = APIRouter(prefix="/api/veeramangai")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def identity(authorization: str | None = Header(None)):
    try:
        who = auth.from_header(authorization)
    except auth.AuthError:
        raise HTTPException(401, "Please sign in again.") from None
    if not who:
        raise HTTPException(401, "Sign in to use saved requests.")
    return who


def coordinator_id():
    value = config.env("VM_COORDINATOR_USER_ID")
    try:
        return str(UUID(value)) if value else None
    except ValueError:
        return None


def require_coordinator(who=Depends(identity)):
    if not coordinator_id() or who["auth_id"] != coordinator_id():
        raise HTTPException(403, "Coordinator access is required.")
    return who


def worker(x_vm_automation: str | None = Header(None)):
    secret = config.env("VM_AUTOMATION_SECRET")
    if len(secret) < 32 or not x_vm_automation or not hmac.compare_digest(secret, x_vm_automation):
        raise HTTPException(401, "Automation authentication required.")


def enabled():
    return config.env("VM_NOTIFICATIONS_ENABLED").lower() == "true"


def notify(event_id):
    """A wake-up only; the database outbox is authoritative if n8n is unavailable."""
    target = config.env("VM_N8N_NOTIFICATIONS_URL")
    key = config.env("VM_N8N_WEBHOOK_SECRET")
    parsed = urlparse(target)
    if not enabled() or len(key) < 32 or parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return
    try:
        httpx.post(target, headers={"X-VM-Webhook": key}, json={"event_id": str(event_id)},
                   timeout=8, follow_redirects=False)
    except httpx.HTTPError:
        pass  # Replay the durable pending outbox manually; no blind Gmail retry.


class Profile(StrictModel):
    display_name: str = Field(min_length=1, max_length=50)
    district_id: str | None = Field(None, max_length=80)
    sport_id: str | None = Field(None, max_length=80)
    language: Literal["ta", "en"] = "ta"
    email_updates: bool = False


@router.get("/workspace")
def workspace(who=Depends(identity)):
    rows = db.call("vm_athlete_profiles", params={"select": "*", "user_id": "eq." + who["auth_id"]})
    return {"profile": rows[0] if rows else None,
            "coordinator_configured": bool(coordinator_id()),
            "is_coordinator": who["auth_id"] == coordinator_id(),
            "email_confirmed": bool(who.get("email_confirmed"))}


@router.put("/profile")
def save_profile(body: Profile, who=Depends(identity)):
    if body.email_updates and not (who.get("email_confirmed") and who.get("email")):
        raise HTTPException(422, "Confirm your account email before enabling email updates.")
    result = db.rpc("vm_save_profile", p_actor=who["auth_id"], p_profile=body.model_dump(),
                    p_email=who.get("email") if body.email_updates else None)
    return {"profile": result}


Category = Literal["equipment", "entry_fee", "travel", "lighter_session", "rest", "private_conversation"]


class Submission(StrictModel):
    event_id: UUID
    category: Category
    opportunity_id: str | None = Field(None, max_length=100)
    consent_to_share: Literal[True]


class Transition(StrictModel):
    event_id: UUID
    expected_status: Literal["submitted", "reviewing"]
    status: Literal["reviewing", "approved", "declined", "cancelled"]


@router.post("/requests")
def submit(body: Submission, tasks: BackgroundTasks, who=Depends(identity)):
    cid = coordinator_id()
    if not cid:
        raise HTTPException(503, "A participating coordinator must be configured before submitting requests.")
    result = db.rpc("vm_request_change", p_actor=who["auth_id"], p_event=str(body.event_id), p_action="submit",
                    p_data={"category": body.category, "opportunity_id": body.opportunity_id,
                            "coordinator_id": cid})
    tasks.add_task(notify, body.event_id)
    return result


@router.get("/requests")
def requests(offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=100), who=Depends(identity)):
    return db.page("vm_support_requests", filters={"user_id": "eq." + who["auth_id"]}, offset=offset, limit=limit)


@router.get("/coordinator/requests")
def coordinator_requests(offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=100), who=Depends(require_coordinator)):
    return db.page("vm_support_requests", filters={"coordinator_id": "eq." + who["auth_id"]}, offset=offset, limit=limit)


@router.post("/requests/{request_id}/status")
def change(request_id: UUID, body: Transition, tasks: BackgroundTasks, who=Depends(identity)):
    if body.status != "cancelled" and who["auth_id"] != coordinator_id():
        raise HTTPException(403, "Only the assigned coordinator can respond.")
    result = db.rpc("vm_request_change", p_actor=who["auth_id"], p_event=str(body.event_id), p_action="transition",
                    p_data={"request_id": str(request_id), "status": body.status, "expected_status": body.expected_status})
    tasks.add_task(notify, body.event_id)
    return result


class Claim(StrictModel):
    event_id: UUID | None = None


@router.post("/automation/claim", dependencies=[Depends(worker)])
def claim(body: Claim):
    if not enabled():
        return {"deliveries": [], "state": "notifications_disabled"}
    deliveries = db.rpc("vm_claim_notifications", p_event=str(body.event_id) if body.event_id else None)
    return {"deliveries": deliveries, "state": "claimed"}


class Receipt(StrictModel):
    delivery_id: UUID
    claim_id: UUID
    status: Literal["sent", "uncertain"]
    provider_id: str | None = Field(None, min_length=1, max_length=200)


@router.post("/automation/receipt", dependencies=[Depends(worker)])
def receipt(body: Receipt):
    if body.status == "sent" and not body.provider_id:
        raise HTTPException(422, "Gmail's message ID is required before recording sent.")
    return db.rpc("vm_finish_notification", p_id=str(body.delivery_id), p_claim=str(body.claim_id),
                  p_status=body.status, p_provider=body.provider_id)


@router.get("/automation/status", dependencies=[Depends(worker)])
def automation_status():
    rows = db.call("vm_notification_outbox", params={"select": "id,state,created_at,attempted_at", "state": "in.(pending,sending,uncertain)", "order": "created_at", "limit": 101})
    return {"items": rows[:100], "has_more": len(rows) > 100, "notifications_enabled": enabled(),
            "coordinator_configured": bool(coordinator_id()),
            "services": {name: "configured" if config.has(name) else "missing" for name in ("gemini", "sarvam", "maptiler")},
            "razorpay_mode": config.razorpay_mode()}


class Guide(StrictModel):
    topic: Literal["opportunities", "funding", "travel", "support"]
    lang: Literal["ta", "en"] = "ta"


@router.post("/automation/guide", dependencies=[Depends(worker)])
def guide(body: Guide):
    from .veeramangai import chat, Message
    prompts = {"opportunities": "Find a trial", "funding": "Help with entry fees", "travel": "Plan travel", "support": "Ask for rest"}
    return chat(Message(text=prompts[body.topic], lang=body.lang))


@router.post("/automation/speech", dependencies=[Depends(worker)])
def speech(body: Guide):
    # Uses fixed guidance, not arbitrary private text or instructions from the client.
    from .agents.voice import tts
    messages = {"en": "Sign in to save your profile, submit a support request and review your coordinator's response. Sample opportunities are for demonstration only.",
                "ta": "உங்கள் விவரங்களைச் சேமித்து, உதவி கோரிக்கையை அனுப்ப உள்நுழையுங்கள். ஒருங்கிணைப்பாளரின் பதிலை உங்கள் பக்கத்தில் பார்க்கலாம். மாதிரி போட்டிகள் விளக்கத்திற்கு மட்டும்."}
    return tts(messages[body.lang], body.lang)
