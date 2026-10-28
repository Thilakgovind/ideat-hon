"""Circle agent: trusted contacts, Journey Watch (start / check-in / alert) and SOS.

In-memory store seeded from data/circle.json (V1; Supabase later).
Journey Watch: at ETA -> reminder to her; ETA + 10 min -> alert to her circle.
"""
import copy
import hashlib
import uuid
from datetime import timedelta

import httpx

from .. import config, data, store
from ..guardrails import describe_delivery, filter_location, location_allowed, needs_confirmation
from . import sms, safety

ALERT_AFTER_ETA_MIN = 10
HELP_RADIUS_M = 1500
# Same list as frontend/src/lib/helplines.js (EMERGENCY).
HELPLINES = [{"name": "Emergency", "number": "112"}, {"name": "Women helpline", "number": "181"},
             {"name": "Women police", "number": "1091"}, {"name": "Police", "number": "100"}]


class Store:
    def __init__(self):
        self.reset()

    def reset(self):
        seed = data.circle_seed()
        self.max_contacts = seed["max_contacts"]
        self.users = {u["user_id"]: copy.deepcopy(u) for u in seed["users"]}
        self.trips = {}
        self.sos = {}

    def user(self, user_id: str) -> dict:
        if user_id not in self.users:
            self.users[user_id] = {"user_id": user_id, "display_name": "", "home_area": None, "contacts": []}
        return self.users[user_id]


STORE = Store()


def user_id_for_phone(phone: str) -> str:
    """Pseudonymous id for an SMS user. The phone itself is never logged."""
    return "u_" + hashlib.sha256((phone or "").encode()).hexdigest()[:12]


def _public_contact(c):
    return {k: v for k, v in c.items() if k != "phone"}


N8N_STATUS = {"sent": 0, "failed": 0}


def _post_n8n(event, payload):
    try:
        r = httpx.post(config.env("N8N_WEBHOOK_URL"), json={"event": event, **payload}, timeout=8)
        N8N_STATUS["sent" if r.status_code < 300 else "failed"] += 1
    except httpx.HTTPError:
        N8N_STATUS["failed"] += 1


def _notify_n8n(event: str, payload: dict):
    """Trip events to n8n (N8N_WEBHOOK_URL), in the background. Payloads never carry phones or names."""
    if not config.has("n8n"):
        return {"status": "mock_logged"}
    store._pool.submit(_post_n8n, event, payload)
    return {"status": "queued"}


# ---------- contacts ----------

def list_circle(user_id: str) -> dict:
    u = STORE.user(user_id)
    contacts = [_public_contact(c) for c in u["contacts"]]
    return {"user_id": user_id, "contacts": contacts, "max": STORE.max_contacts,
            "slots_left": STORE.max_contacts - len(contacts),
            "how_sharing_works": [
                "Both sides must accept before anything is shared.",
                "Your circle sees you only during a trip or SOS.",
                "Max 5 people. Remove anyone anytime."],
            "source": "sample"}


def add_contact(user_id, label, phone=None, relation="friend", confirmed=False) -> dict:
    u = STORE.user(user_id)
    if len(u["contacts"]) >= STORE.max_contacts:
        return {"error": "circle_full", "max": STORE.max_contacts}
    preview = f"{u.get('display_name') or 'A SafePath user'} invited you to her SafePath circle. Reply YES to accept."
    if needs_confirmation("invite", confirmed):
        return {"needs_confirmation": True, "action": "invite", "preview": preview, "to": label}
    c = {"id": "c" + uuid.uuid4().hex[:6], "label": label, "relation": relation, "phone": phone,
         "phone_masked": sms.mask(phone), "accepted": False, "status": "invite_pending",
         "area": None, "lat": None, "lng": None, "source": "runtime"}
    u["contacts"].append(c)
    _ensure_user(user_id)
    store.persist("circle_contacts", _contact_row(user_id, c))
    delivery = sms.send(phone, preview, purpose="invite")
    return {"contact": _public_contact(c), "invite": {"status": delivery["status"]}}


def accept_contact(user_id, contact_id) -> dict:
    for c in STORE.user(user_id)["contacts"]:
        if c["id"] == contact_id:
            c["accepted"], c["status"] = True, "available"
            store.persist("circle_contacts", _contact_row(user_id, c))
            return {"contact": _public_contact(c)}
    return {"error": "not_found"}


def remove_contact(user_id, contact_id) -> dict:
    u = STORE.user(user_id)
    before = len(u["contacts"])
    u["contacts"] = [c for c in u["contacts"] if c["id"] != contact_id]
    store.delete("circle_contacts", contact_id)
    return {"removed": before != len(u["contacts"])}


MESSAGES = {
    "meet": "{name} is walking home on {where}. Can you meet her on the way? (SafePath)",
    "call_me": "{name} asked you to call her now. (SafePath)",
}


def message_contact(user_id, contact_id, kind="meet", where="the main road", confirmed=False) -> dict:
    """Send one fixed, pre-written message to an accepted contact. Needs confirmation."""
    u = STORE.user(user_id)
    c = next((x for x in u["contacts"] if x["id"] == contact_id), None)
    if not c or not c.get("accepted"):
        return {"error": "not_in_circle"}
    if kind not in MESSAGES:
        return {"error": "unknown_message"}
    body = MESSAGES[kind].format(name=u.get("display_name") or "Your contact", where=where)
    if needs_confirmation("message", confirmed):
        return {"needs_confirmation": True, "action": "message", "preview": body, "to": c["label"]}
    r = sms.send(c.get("phone"), body, purpose=f"message_{kind}")
    return {"to": c["label"], "status": r["status"], "delivery": describe_delivery([r])}


def _trip_row(t):
    return {"id": t["trip_id"], "user_id": t["user_id"], "option_id": t.get("option_id"), "kind": t.get("kind"),
            "summary": t.get("summary"), "from_area": t.get("from"), "to_area": t.get("to"), "alight_stop": t.get("alight_code"),
            "start_at": t["start"].isoformat(), "eta_at": t["eta"].isoformat(), "status": t["status"],
            "notified_circle": t.get("notified_circle", False), "reminded": t.get("reminded", False),
            "distance_m": t.get("distance_m"), "last_lat": (t.get("last_location") or {}).get("lat"),
            "last_lng": (t.get("last_location") or {}).get("lng"), "last_checkin_at": t.get("last_checkin"), "source": "live"}


def _event(trip, ev):
    """Record a trip event in memory and mirror trip + event to Supabase (no phone numbers)."""
    trip["events"].append(ev)
    store.persist("trips", _trip_row(trip))
    detail = {k: v for k, v in ev.items() if k not in ("at", "event")}
    store.persist("trip_events", {"trip_id": trip["trip_id"], "at": ev["at"], "event": ev["event"], "detail": detail,
                                  "source": "live"}, method="insert")


def _contact_row(user_id, c):
    return {"id": c["id"], "user_id": user_id, "label": c["label"], "label_ta": c.get("label_ta"), "relation": c.get("relation"),
            "phone": c.get("phone"), "accepted": c.get("accepted", False), "status": c.get("status"), "area": c.get("area"),
            "lat": c.get("lat"), "lng": c.get("lng"), "source": c.get("source") if c.get("source") == "sample" else "live"}


def _ensure_user(user_id):
    u = STORE.user(user_id)
    store.persist("users", {"id": user_id, "display_name": u.get("display_name") or None, "phone": None,
                            "home_area": u.get("home_area"), "start_area": u.get("start_area"), "lang": "en",
                            "source": "sample" if user_id == "u_demo" else "live"})


def _watchers(user_id):
    return [c for c in STORE.user(user_id)["contacts"] if c.get("accepted")]


def _send_all(contacts, body, purpose):
    results = []
    for c in contacts:
        r = sms.send(c.get("phone"), body, purpose=purpose)
        results.append({"contact_id": c["id"], "label": c["label"], "status": r["status"]})
    return results


# ---------- Journey Watch ----------

def start_trip(user_id, option: dict, frm: str, to: str, confirmed=False, notify_circle=True,
               user_phone=None, now=None) -> dict:
    now = now or data.now_ist()
    u = STORE.user(user_id)
    watchers = _watchers(user_id)
    summary = _trip_summary(option, frm, to)
    name = u.get("display_name") or "Your contact"
    eta_min = _eta_minutes(option, now)
    eta = now + timedelta(minutes=eta_min)
    message = f"{name} started a trip: {summary}. ETA {eta.strftime('%H:%M')}. SafePath will tell you when she reaches."
    if notify_circle and watchers and needs_confirmation("message", confirmed):
        return {"needs_confirmation": True, "action": "message", "preview": message,
                "to": [c["label"] for c in watchers]}
    trip_id = "t_" + uuid.uuid4().hex[:8]
    trip = {
        "trip_id": trip_id, "user_id": user_id, "option_id": option.get("id"), "summary": summary,
        "from": frm, "to": to, "legs": option.get("legs", []), "alight_code": option.get("alight_code"),
        "start": now, "eta": eta, "status": "active", "reminded": False, "alerted": False,
        "notified_circle": bool(notify_circle and watchers), "user_phone": user_phone,
        "last_location": None, "last_checkin": None, "events": [],
        "kind": option.get("kind"), "path_id": option.get("path_id"), "distance_m": _distance_m(option, frm, to),
        "eta_min": eta_min,
    }
    STORE.trips[trip_id] = trip
    _ensure_user(user_id)
    results = _send_all(watchers, message, "trip_start") if trip["notified_circle"] else []
    _event(trip, {"at": now.isoformat(), "event": "start", "delivery": describe_delivery(results)})
    _notify_n8n("trip_start", {"trip_id": trip_id, "eta": eta.isoformat()})
    return {"trip": public_trip(trip), "circle_delivery": results, "delivery": describe_delivery(results)}


def _trip_summary(option, frm, to):
    labels = [l["label"] for l in option.get("legs", []) if l["mode"] != "walk"]
    return f"{' + '.join(labels) or 'Trip'} {frm} -> {to}"


def _distance_m(option, frm, to):
    if option.get("distance_m"):
        return option["distance_m"]
    if option.get("distance_km"):
        return int(option["distance_km"] * 1000)
    a, b = data.area_coords(frm or ""), data.area_coords(to or "")
    return int(data.haversine_m(*a, *b) * 1.35) if a and b else None


def _eta_minutes(option, now):
    reach = option.get("reach_by")
    if not reach:
        return option.get("total_min", 30)
    total = option.get("total_min", 0)
    diff = (data.to_minutes(reach) - (now.hour * 60 + now.minute)) % (24 * 60)
    # planned for a different time but started now: ride time from now
    return total if diff > total + 60 else max(diff, total)


def public_trip(trip: dict) -> dict:
    out = {k: v for k, v in trip.items() if k not in ("user_phone",)}
    out["start"] = trip["start"].isoformat()
    out["eta"] = trip["eta"].isoformat()
    out["eta_hhmm"] = trip["eta"].strftime("%H:%M")
    out["watchers"] = [_public_contact(c) for c in _watchers(trip["user_id"])]
    stop = trip.get("alight_code")
    open_now = [p for p in safety.rank_places(safety.places_near_stop(stop or ""), data.parse_time(None)) if p["open_now"]]
    out["next_open_shop"] = ({"id": open_now[0]["id"], "name": open_now[0]["name"]} if open_now else None)
    return out


def get_trip(trip_id: str):
    t = STORE.trips.get(trip_id)
    return public_trip(t) if t else None


def checkin(trip_id: str, ok: bool = True, lat=None, lng=None, now=None) -> dict:
    trip = STORE.trips.get(trip_id)
    if not trip:
        return {"error": "not_found"}
    now = now or data.now_ist()
    active = trip["status"] == "active"
    loc = filter_location({"lat": lat, "lng": lng}, location_allowed(trip_active=active))
    if loc.get("lat") is not None:
        trip["last_location"] = {"lat": loc["lat"], "lng": loc["lng"], "at": now.isoformat()}
    trip["last_checkin"] = now.isoformat()
    _event(trip, {"at": now.isoformat(), "event": "checkin", "ok": ok})
    return {"trip": public_trip(trip), "location_stored": trip["last_location"] is not None and active}


def reached(trip_id: str, now=None) -> dict:
    trip = STORE.trips.get(trip_id)
    if not trip:
        return {"error": "not_found"}
    now = now or data.now_ist()
    trip["status"] = "reached"
    trip["last_location"] = None  # stop sharing location
    results = []
    if trip["notified_circle"]:
        name = STORE.user(trip["user_id"]).get("display_name") or "Your contact"
        results = _send_all(_watchers(trip["user_id"]), f"{name} reached {trip['to']} safely at {now.strftime('%H:%M')}.", "reached")
    _event(trip, {"at": now.isoformat(), "event": "reached", "delivery": describe_delivery(results)})
    _notify_n8n("trip_reached", {"trip_id": trip_id})
    return {"trip": public_trip(trip), "circle_delivery": results, "delivery": describe_delivery(results)}


def find_active_trip(user_id: str):
    for t in STORE.trips.values():
        if t["user_id"] == user_id and t["status"] == "active":
            return t
    return None


def tick(now=None) -> list:
    """Journey Watch timer. Called every 30 s by the server (and by tests with a fake now)."""
    now = now or data.now_ist()
    actions = []
    for trip in list(STORE.trips.values()):
        if trip["status"] != "active":
            continue
        if not trip["reminded"] and now >= trip["eta"]:
            trip["reminded"] = True
            r = sms.send(trip.get("user_phone"), "SafePath: Have you reached? Reply REACHED. Reply HELP if you need help.", "reminder")
            actions.append({"trip_id": trip["trip_id"], "action": "reminder", "status": r["status"]})
            _event(trip, {"at": now.isoformat(), "event": "reminder", "status": r["status"]})
        if now >= trip["eta"] + timedelta(minutes=ALERT_AFTER_ETA_MIN):
            trip["status"], trip["alerted"] = "alerted", True
            name = STORE.user(trip["user_id"]).get("display_name") or "Your contact"
            last = trip["last_location"]
            where = f"Last check-in {trip['last_checkin'][11:16]}" if trip["last_checkin"] else f"Started from {trip['from']} at {trip['start'].strftime('%H:%M')}"
            body = f"SafePath alert: {name} has not confirmed reaching {trip['to']}. {where}. Please call her."
            results = _send_all(_watchers(trip["user_id"]), body, "journey_alert")
            _event(trip, {"at": now.isoformat(), "event": "alert", "delivery": describe_delivery(results),
                                   "had_location": bool(last)})
            actions.append({"trip_id": trip["trip_id"], "action": "alert", "delivery": describe_delivery(results)})
            _notify_n8n("trip_alert", {"trip_id": trip["trip_id"]})
    return actions


# ---------- SOS ----------

def sos(user_id: str, lat=None, lng=None, trip_id=None, now=None) -> dict:
    """SOS skips confirmation: alert circle, show helplines, share location until stopped."""
    now = now or data.now_ist()
    name = STORE.user(user_id).get("display_name") or "Your contact"
    trip = STORE.trips.get(trip_id) if trip_id else find_active_trip(user_id)
    point = (lat, lng) if lat is not None and lng is not None else None
    if point is None and trip and trip.get("last_location"):
        point = (trip["last_location"]["lat"], trip["last_location"]["lng"])
    where = f" near {trip['to']}" if trip else ""
    body = f"SOS from {name}{where} at {now.strftime('%H:%M')}. Please call her now. Women helpline 181, Police 100."
    results = _send_all(_watchers(user_id), body, "sos")
    if trip:
        _event(trip, {"at": now.isoformat(), "event": "sos", "delivery": describe_delivery(results)})
    STORE.sos[user_id] = {"active": True, "since": now.isoformat(), "location": {"lat": point[0], "lng": point[1]} if point else None}
    if point is None and trip:  # no live location: look for help around the trip's destination area
        point = data.area_coords(trip["to"])
    _notify_n8n("sos", {"user": user_id, "at": now.isoformat()})
    return {"sos": STORE.sos[user_id], "circle_delivery": results, "delivery": describe_delivery(results),
            "helplines": HELPLINES, "nearest_help": nearest_help(point, now), "confirmation_skipped": True}


def sos_stop(user_id: str, now=None) -> dict:
    now = now or data.now_ist()
    state = STORE.sos.get(user_id)
    if not state or not state.get("active"):
        return {"sos": {"active": False}}
    state.update({"active": False, "location": None, "ended": now.isoformat()})
    name = STORE.user(user_id).get("display_name") or "Your contact"
    results = _send_all(_watchers(user_id), f"{name} is safe now ({now.strftime('%H:%M')}). SOS ended.", "sos_end")
    return {"sos": state, "circle_delivery": results, "delivery": describe_delivery(results)}


def nearest_help(point, now=None):
    now = now or data.now_ist()
    minutes = now.hour * 60 + now.minute
    point = point or (13.0878, 80.2006)
    helpful = [p for p in data.places()
               if p["type"] in ("police_booth", "hospital", "pharmacy", "shg_kiosk", "petrol_bunk") and safety.is_open(p, minutes)
               and data.haversine_m(point[0], point[1], p["lat"], p["lng"]) <= HELP_RADIUS_M]
    helpful.sort(key=lambda p: data.haversine_m(point[0], point[1], p["lat"], p["lng"]))
    return [{"id": p["id"], "name": p["name"], "type": p["type"],
             "distance_m": int(data.haversine_m(point[0], point[1], p["lat"], p["lng"]))} for p in helpful[:3]]
