"""SafePath V1.1 API server (FastAPI).

Run from the repo root:
    .venv/Scripts/python -m uvicorn backend.app:app --reload --port 8000
"""
import asyncio
import contextlib
import contextvars
import hashlib
from collections import deque
from typing import Optional

import httpx

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from . import auth, config, data, orchestrator, store
from .agents import callback, circle, pay, places, route, safety, sms, voice

DEMO_USER = "u_demo"
CURRENT = contextvars.ContextVar("current_user", default=None)  # set per request from the Supabase token
TICK_SECONDS = 30
REFRESH_SECONDS = 600
SEEN_INBOUND: deque = deque(maxlen=300)  # de-duplicate provider retries


@contextlib.asynccontextmanager
async def lifespan(_app):
    config.assert_safe_to_start()
    await asyncio.to_thread(store.load_public)  # Supabase when reachable, else /data JSON

    async def ticker():
        since_refresh = 0
        while True:
            await asyncio.sleep(TICK_SECONDS)
            await asyncio.to_thread(circle.tick)
            since_refresh += TICK_SECONDS
            if since_refresh >= REFRESH_SECONDS:
                since_refresh = 0
                await asyncio.to_thread(store.load_public)

    task = asyncio.create_task(ticker())
    yield
    task.cancel()


app = FastAPI(title="SafePath V1.1 API", version="1.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def supabase_user(request: Request, call_next):
    """Signed-in requests act as her own user; no token = the demo user. A bad token is refused."""
    try:
        who = await asyncio.to_thread(auth.from_header, request.headers.get("authorization"))
    except auth.AuthError as e:
        return JSONResponse({"detail": "please sign in again", "reason": str(e)}, status_code=401)
    token = CURRENT.set(who)
    try:
        return await call_next(request)
    finally:
        CURRENT.reset(token)


def _uid(_claimed=None) -> str:
    """The acting user: from the verified token, else the demo user. Client-sent ids are ignored."""
    who = CURRENT.get()
    return who["user_id"] if who else DEMO_USER


# ---------- models ----------

class ChatIn(BaseModel):
    text: str = Field(..., max_length=500)
    lang: Optional[str] = "en"
    user_id: Optional[str] = DEMO_USER


class TripRef(BaseModel):
    from_: str = Field(..., alias="from")
    to: str
    time: Optional[str] = None
    option_id: str


class TripStartIn(TripRef):
    confirmed: bool = False
    notify_circle: bool = True
    user_id: Optional[str] = DEMO_USER


class CheckinIn(BaseModel):
    trip_id: str
    ok: bool = True
    lat: Optional[float] = None
    lng: Optional[float] = None


class ReachedIn(BaseModel):
    trip_id: str


class SosIn(BaseModel):
    action: str = "start"  # start | stop
    lat: Optional[float] = None
    lng: Optional[float] = None
    trip_id: Optional[str] = None
    user_id: Optional[str] = DEMO_USER


class CircleIn(BaseModel):
    action: str  # add | accept | remove | message
    kind: Optional[str] = "meet"
    where: Optional[str] = None
    label: Optional[str] = None
    phone: Optional[str] = None
    relation: Optional[str] = "friend"
    contact_id: Optional[str] = None
    confirmed: bool = False
    user_id: Optional[str] = DEMO_USER


class PayOrderIn(TripRef):
    confirmed: bool = False


class PayVerifyIn(BaseModel):
    order_id: str
    payment_id: str
    signature: str


# ---------- endpoints ----------

@app.get("/health")
def health():
    ok, why = callback.ready()
    return {"status": "ok", "version": "1.1.0", "demo_mode": config.demo_mode(),
            "services": config.services_status(), "storage": store.status(),
            "call_back": "ready" if ok else f"off ({why})", "data": "sample"}


@app.get("/api/profile")
def profile():
    """Profile: name, usual start, home and saved places. No phone numbers."""
    user_id = _uid()
    u = circle.STORE.user(user_id)
    return {"user_id": user_id, "display_name": u.get("display_name"), "home_area": u.get("home_area"),
            "start_area": u.get("start_area"), "saved_places": u.get("saved_places", []), "source": "sample"}


class MeIn(BaseModel):
    display_name: Optional[str] = Field(None, max_length=40)
    home_area: Optional[str] = Field(None, max_length=60)
    start_area: Optional[str] = Field(None, max_length=60)
    lang: Optional[str] = Field(None, pattern="^(en|ta)$")


def _me_payload(user_id: str, who) -> dict:
    u = circle.STORE.user(user_id)
    return {"user_id": user_id, "signed_in": bool(who), "auth": "supabase" if who else "demo",
            "phone_masked": auth.mask_phone(who.get("phone")) if who else None,
            "display_name": u.get("display_name") or None, "home_area": u.get("home_area"),
            "start_area": u.get("start_area"), "lang": u.get("lang") or "en",
            "needs_setup": bool(who) and not u.get("display_name")}


@app.get("/api/auth/config")
def auth_config():
    """What the login screen can offer. No keys here: the browser gets the anon key from Vite."""
    return {"supabase": auth.enabled(), "demo_login": True}


@app.get("/api/me")
def me():
    who = CURRENT.get()
    uid = _uid()
    if who:
        saved = store.load_user(uid)
        if saved:
            u = circle.STORE.user(uid)
            for k in ("display_name", "home_area", "start_area", "lang"):
                if saved.get(k) and not u.get(k):
                    u[k] = saved[k]
    return _me_payload(uid, who)


@app.put("/api/me")
def me_update(body: MeIn):
    who = CURRENT.get()
    if not who:
        raise HTTPException(401, "sign in to save your profile")
    uid = _uid()
    u = circle.STORE.user(uid)
    for k, v in body.model_dump(exclude_none=True).items():
        u[k] = v.strip() if isinstance(v, str) else v
    # Phone lives only in users.phone (private, service key). Never logged or returned in full.
    store.persist("users", {"id": uid, "display_name": u.get("display_name"), "phone": who.get("phone"),
                            "home_area": u.get("home_area"), "start_area": u.get("start_area"),
                            "lang": u.get("lang") or "en", "source": "live"})
    return _me_payload(uid, who)


@app.post("/api/aval/chat")
def aval_chat(body: ChatIn):
    return orchestrator.handle(body.text, lang=body.lang, channel="app", user_id=_uid())


@app.post("/api/aval/voice")
async def aval_voice(audio: UploadFile = File(None), lang: str = Form("ta"), hint: Optional[str] = Form(None),
                     user_id: str = Form(DEMO_USER)):
    raw = await audio.read() if audio else b""
    heard = voice.stt(raw, audio.filename if audio else "audio.wav",
                      audio.content_type if audio else "audio/wav", lang=lang, hint=hint)
    result = orchestrator.handle(heard["text"], lang=lang, channel="voice", user_id=_uid())
    spoken = voice.tts(result["reply"]["text"], lang=result["reply"]["lang"])
    return {**result, "transcript": heard["text"], "stt_provider": heard["provider"],
            "tts_provider": spoken["provider"], "audio_base64": spoken.get("audio_base64"),
            "audio_format": spoken.get("format")}


@app.get("/api/routes")
def get_routes(from_: Optional[str] = Query(None, alias="from"), to: Optional[str] = None, time: Optional[str] = None,
               sort: str = "safest", with_child: bool = False, mode: Optional[str] = None,
               free_only: bool = False):
    if not from_:
        raise HTTPException(400, "from is required")
    if not to:
        return route.arrivals(from_, time, free_only)
    plan = route.plan(from_, to, time, with_child, modes=[mode] if mode else None)
    if plan.get("error"):
        return plan
    plan["options"] = safety.rank_options(plan["options"], data.to_minutes(plan["time"]), sort, with_child)
    plan["sort"] = sort
    return plan


@app.get("/api/safe-route")
def safe_route(from_: Optional[str] = Query(None, alias="from"), to: Optional[str] = None, time: Optional[str] = None):
    minutes = data.parse_time(time)
    user = circle.STORE.user(_uid())
    out = {"time": data.fmt_minutes(minutes), "source": "sample"}
    if from_ and to:
        plan = route.plan(from_, to, time)
        if not plan.get("error"):
            out["transit"] = safety.rank_options(plan["options"], minutes, "safest")
    area = route.match_place(to or user.get("home_area") or "Nungambakkam")
    code = orchestrator._stop_code_for(area) if area else None
    out["walk"] = safety.compare_walk_paths(code or "", minutes, user["contacts"])
    out["to"] = area
    return out


@app.get("/api/places")
def get_places(lat: Optional[float] = None, lng: Optional[float] = None, open_now: bool = False,
               type: Optional[str] = None, chip: Optional[str] = None, women_run: Optional[bool] = None,
               well_lit: Optional[bool] = None, radius_m: int = 2000, time: Optional[str] = None,
               near: Optional[str] = None):
    if near and lat is None:
        area = route.match_place(near)
        coords = data.area_coords(area) if area else None
        if not coords:
            raise HTTPException(404, "place not found")
        lat, lng = coords
    return places.search(lat, lng, radius_m, open_now, type, chip, women_run, well_lit, time=time)


@app.get("/api/places/{place_id}")
def get_place(place_id: str, time: Optional[str] = None):
    d = places.details(place_id, time)
    if d.get("error"):
        raise HTTPException(404, "place not found")
    return d


def _option_or_404(ref: TripRef):
    option, _plan = route.find_option(ref.from_, ref.to, ref.time, ref.option_id)
    if not option:
        raise HTTPException(404, "option not found - plan the trip again")
    return option


@app.post("/api/trip/start")
def trip_start(body: TripStartIn):
    option = _option_or_404(body)
    return circle.start_trip(_uid(), option, route.match_place(body.from_), route.match_place(body.to),
                             confirmed=body.confirmed, notify_circle=body.notify_circle)


@app.get("/api/trip/{trip_id}")
def trip_get(trip_id: str):
    t = circle.get_trip(trip_id)
    if not t:
        raise HTTPException(404, "trip not found")
    return {"trip": t}


@app.post("/api/trip/checkin")
def trip_checkin(body: CheckinIn):
    res = circle.checkin(body.trip_id, body.ok, body.lat, body.lng)
    if res.get("error"):
        raise HTTPException(404, "trip not found")
    return res


@app.post("/api/trip/reached")
def trip_reached(body: ReachedIn):
    res = circle.reached(body.trip_id)
    if res.get("error"):
        raise HTTPException(404, "trip not found")
    return res


@app.post("/api/sos")
def sos(body: SosIn):
    uid = _uid()
    if body.action == "stop":
        return circle.sos_stop(uid)
    return circle.sos(uid, body.lat, body.lng, body.trip_id)


@app.get("/api/circle")
def circle_get():
    return circle.list_circle(_uid())


@app.post("/api/circle")
def circle_post(body: CircleIn):
    uid = _uid()
    if body.action == "add":
        if not body.label:
            raise HTTPException(400, "label is required")
        return circle.add_contact(uid, body.label, body.phone, body.relation, body.confirmed)
    if body.action == "accept":
        return circle.accept_contact(uid, body.contact_id)
    if body.action == "remove":
        return circle.remove_contact(uid, body.contact_id)
    if body.action == "message":
        res = circle.message_contact(uid, body.contact_id, body.kind, body.where or "the main road", body.confirmed)
        if res.get("error"):
            raise HTTPException(400, res["error"])
        return res
    raise HTTPException(400, "action must be add, accept, remove or message")


@app.post("/api/pay/order")
def pay_order(body: PayOrderIn):
    option = _option_or_404(body)
    return pay.create_order(option, route.match_place(body.from_), route.match_place(body.to), body.confirmed, body.time)


@app.post("/api/pay/verify")
def pay_verify(body: PayVerifyIn):
    res = pay.verify(body.order_id, body.payment_id, body.signature)
    if res.get("error") == "order_not_found":
        raise HTTPException(404, "order not found")
    if res.get("error"):
        raise HTTPException(400, res["error"])
    return res


@app.get("/api/tickets")
def tickets_list():
    """Tickets issued in this server session (newest first)."""
    return {"tickets": list(reversed(list(pay.TICKETS.values()))), "source": "sample"}


@app.get("/api/tickets/{ticket_id}")
def ticket_get(ticket_id: str):
    t = pay.TICKETS.get(ticket_id)
    if not t:
        raise HTTPException(404, "ticket not found")
    return {"ticket": t}


def _public_url(request: Request) -> str:
    q = request.url.query
    return config.env("PUBLIC_BACKEND_URL").rstrip("/") + request.url.path + (f"?{q}" if q else "")


async def _twilio_form(request: Request) -> dict:
    form = {k: v for k, v in (await request.form()).items()}
    if not sms.verify_twilio(_public_url(request), form, request.headers.get("X-Twilio-Signature", "")):
        raise HTTPException(403, "bad Twilio signature")
    return form


@app.post("/api/sms/webhook")
async def sms_webhook(request: Request):
    """Twilio inbound SMS -> orchestrator -> TwiML reply."""
    form = await _twilio_form(request)
    msg = sms.parse_inbound(form)
    uid = circle.user_id_for_phone(msg["from"])
    result = orchestrator.handle(msg["body"], channel="sms", user_id=uid, user_phone=msg["from"] or None)
    return Response(content=sms.twiml(result["sms_text"]), media_type="application/xml")


@app.post("/api/sms/textbee")
async def sms_textbee(request: Request):
    """textbee inbound SMS webhook -> orchestrator -> reply via the selected SMS provider.
    Junk / non-SMS payloads are ignored (200, so textbee does not retry them)."""
    raw = await request.body()
    sig = request.headers.get("x-signature") or request.headers.get("x-textbee-signature") or ""
    if not sms.verify_textbee(raw, sig):
        raise HTTPException(403, "bad signature")
    try:
        payload = await request.json()
    except ValueError:
        return {"ok": True, "ignored": "not json"}
    msg = sms.parse_textbee(payload)
    if not msg:
        return {"ok": True, "ignored": "not an inbound sms"}
    key = hashlib.sha256(raw).hexdigest()
    if key in SEEN_INBOUND:
        return {"ok": True, "ignored": "duplicate"}
    SEEN_INBOUND.append(key)
    uid = circle.user_id_for_phone(msg["from"])
    result = await asyncio.to_thread(orchestrator.handle, msg["body"], None, "sms", uid, msg["from"])
    sent = await asyncio.to_thread(sms.send, msg["from"], result["sms_text"], "reply")
    return {"ok": True, "intent": result["intake"]["intent"], "reply_status": sent["status"]}


# ---------- voice call-back (Twilio + Sarvam) ----------

def _xml(body: str) -> Response:
    return Response(content=body, media_type="application/xml")


@app.post("/api/voice/call/start")
async def call_start(request: Request, lang: str = "ta"):
    await _twilio_form(request)
    return _xml(await asyncio.to_thread(callback.twiml_start, lang))


@app.post("/api/voice/call/recorded")
async def call_recorded(request: Request, lang: str = "ta"):
    form = await _twilio_form(request)
    return _xml(callback.twiml_recorded(form.get("RecordingUrl", ""), form.get("To") or form.get("Called") or "", lang))


@app.post("/api/voice/call/answer")
async def call_answer(request: Request, job: str = "", lang: str = "ta"):
    await _twilio_form(request)
    return _xml(callback.twiml_answer(job, lang))


@app.get("/api/voice/audio/{clip_id}.wav")
def call_audio(clip_id: str):
    clip = callback.AUDIO.get(clip_id)
    if not clip:
        raise HTTPException(404, "audio expired")
    return Response(content=clip, media_type="audio/wav")


# ---------- demo page ----------

class DemoIn(BaseModel):
    text: str = Field(..., max_length=500)
    lang: Optional[str] = "en"


def _from_n8n(body: dict) -> dict:
    """Normalise the n8n orchestrator reply to our chat shape."""
    reply = body.get("reply")
    if isinstance(reply, str):
        reply = {"text": reply, "lang": "en"}
    if not isinstance(reply, dict) or not body.get("sms_text"):
        raise ValueError("unexpected n8n reply")
    steps = body.get("agent_steps") or body.get("steps") or []
    return {"reply": reply, "sms_text": body["sms_text"], "card": body.get("card"), "actions": body.get("actions") or [],
            "aval_state": body.get("aval_state", "talking"), "steps": steps, "agent_steps": steps,
            "fallback": bool(body.get("fallback")), "sample_data": True}


@app.post("/api/demo/chat")
async def demo_chat(body: DemoIn):
    """Demo page (keypad phone). Routes through n8n when N8N_ORCHESTRATOR_URL is set; falls back to the backend."""
    url = config.env("N8N_ORCHESTRATOR_URL")
    why = None
    if url:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(url, json={"text": body.text, "lang": body.lang, "channel": "sms"})
            if r.status_code < 300:
                return {**_from_n8n(r.json()), "via": "n8n"}
            why = f"n8n HTTP {r.status_code}"
        except (httpx.HTTPError, ValueError) as e:
            why = f"n8n {type(e).__name__}"
    result = await asyncio.to_thread(orchestrator.handle, body.text, body.lang, "sms", "u_demo_keypad", None)
    return {**result, "via": "backend" if not why else f"backend ({why})"}


@app.get("/api/demo/outbox")
def demo_outbox():
    """What the SMS agent sent or logged (phones masked). For the judges' demo panel."""
    return {"messages": list(sms.OUTBOX)[-50:], "provider": config.sms_provider()}
