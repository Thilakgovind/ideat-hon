"""SafePath V1 API server (FastAPI).

Run from the repo root:
    .venv/Scripts/python -m uvicorn backend.app:app --reload --port 8000
"""
import asyncio
import contextlib
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from . import config, data, orchestrator
from .agents import circle, pay, places, route, safety, sms, voice

DEMO_USER = "u_demo"
TICK_SECONDS = 30


@contextlib.asynccontextmanager
async def lifespan(_app):
    async def ticker():
        while True:
            await asyncio.sleep(TICK_SECONDS)
            circle.tick()

    task = asyncio.create_task(ticker())
    yield
    task.cancel()


app = FastAPI(title="SafePath V1 API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    return {"status": "ok", "version": "1.0.0", "demo_mode": config.demo_mode(),
            "services": config.services_status(), "data": "sample"}


@app.get("/api/profile")
def profile(user_id: str = DEMO_USER):
    """Demo user profile: name, usual start, home and saved places. No phone numbers."""
    u = circle.STORE.user(user_id)
    return {"user_id": user_id, "display_name": u.get("display_name"), "home_area": u.get("home_area"),
            "start_area": u.get("start_area"), "saved_places": u.get("saved_places", []), "source": "sample"}


@app.post("/api/aval/chat")
def aval_chat(body: ChatIn):
    return orchestrator.handle(body.text, lang=body.lang, channel="app", user_id=body.user_id or DEMO_USER)


@app.post("/api/aval/voice")
async def aval_voice(audio: UploadFile = File(None), lang: str = Form("ta"), hint: Optional[str] = Form(None),
                     user_id: str = Form(DEMO_USER)):
    raw = await audio.read() if audio else b""
    heard = voice.stt(raw, audio.filename if audio else "audio.wav",
                      audio.content_type if audio else "audio/wav", lang=lang, hint=hint)
    result = orchestrator.handle(heard["text"], lang=lang, channel="voice", user_id=user_id)
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
def safe_route(from_: Optional[str] = Query(None, alias="from"), to: Optional[str] = None, time: Optional[str] = None,
               user_id: str = DEMO_USER):
    minutes = data.parse_time(time)
    user = circle.STORE.user(user_id)
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
    return circle.start_trip(body.user_id or DEMO_USER, option, route.match_place(body.from_), route.match_place(body.to),
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
    uid = body.user_id or DEMO_USER
    if body.action == "stop":
        return circle.sos_stop(uid)
    return circle.sos(uid, body.lat, body.lng, body.trip_id)


@app.get("/api/circle")
def circle_get(user_id: str = DEMO_USER):
    return circle.list_circle(user_id)


@app.post("/api/circle")
def circle_post(body: CircleIn):
    uid = body.user_id or DEMO_USER
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


@app.post("/api/sms/webhook")
async def sms_webhook(request: Request):
    form = dict(await request.form())
    msg = sms.parse_inbound(form)
    uid = circle.user_id_for_phone(msg["from"])
    result = orchestrator.handle(msg["body"], channel="sms", user_id=uid, user_phone=msg["from"] or None)
    return Response(content=sms.twiml(result["sms_text"]), media_type="application/xml")


@app.get("/api/demo/outbox")
def demo_outbox():
    """What the SMS agent sent or logged (phones masked). For the judges' demo panel."""
    return {"messages": list(sms.OUTBOX)[-50:], "provider": "twilio" if config.has("twilio") else "mock"}
