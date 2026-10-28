"""Orchestrator: intake -> pick agents -> reply card + "What AVAL did" steps.

Same pipeline for the app chat, Tamil voice and SMS. Facts in replies (buses,
fares, places) always come from the agents' data, never from the LLM.
"""
from . import config, data, guardrails
from .agents import circle, intake, pay, places, route, safety

DEFAULT_START = "Anna Nagar West"  # demo user's usual stop (sample)
SESSIONS: dict = {}  # user_id -> {"last_plan": {...}}

T = {
    "understood": ("Understood your request", "உங்கள் கோரிக்கையைப் புரிந்துகொண்டேன்"),
    "understood_ta": ("Understood your Tamil request", "உங்கள் தமிழ் கோரிக்கையைப் புரிந்துகொண்டேன்"),
    "fallback": (intake.FALLBACK_REPLY, intake.FALLBACK_REPLY_TA),
    "where_to": ("Where do you want to go? Eg: Nungambakkam bus", "எங்கே போக வேண்டும்? உதா: நுங்கம்பாக்கம் பஸ்"),
    "no_route": ("I couldn't find a way in my data for that trip. Try a nearby stop.", "இந்தப் பயணத்துக்கு வழி கிடைக்கவில்லை. அருகிலுள்ள நிறுத்தத்தை முயற்சிக்கவும்."),
    "no_trip": ("Plan a trip first. Eg: Nungambakkam bus", "முதலில் பயணத்தைத் திட்டமிடுங்கள். உதா: நுங்கம்பாக்கம் பஸ்"),
    "help": ("I can find the safest bus, metro or auto, safe places open now, walk you home with your circle watching, and send SOS.",
             "பாதுகாப்பான பஸ், மெட்ரோ, ஆட்டோ, இப்போது திறந்திருக்கும் இடங்கள், உங்கள் வட்டம் பார்க்க வீட்டுக்கு வழி, SOS - எல்லாம் செய்வேன்."),
}


# The only free wording: Vidiyal Payanam covers ordinary (white-board) buses, never "this bus".
FREE_TEXT = "Free for women on ordinary (white-board) buses."
FREE_TEXT_TA = "சாதாரண (வெள்ளை பலகை) பஸ்ஸில் பெண்களுக்கு இலவசம்"
FREE_SMS = "Free for women on white-board buses."

def _hm(hhmm):
    """'08:05' -> '8:05' (how times are written in the app)."""
    return hhmm.lstrip("0") if hhmm and hhmm[0] == "0" and hhmm[1] != ":" else hhmm


def _t(key, ta):
    return T[key][1 if ta else 0]


def _step(text, status="done"):
    return {"text": text, "status": status}


def _session(user_id):
    return SESSIONS.setdefault(user_id, {})


def _stop_code_for(area):
    for r in data.routes():
        for s in r["stops"]:
            if route._belongs(s["name"], area):
                return s["code"]
    return None


def handle(text: str, lang: str = None, channel: str = "app", user_id: str = "u_demo",
           user_phone: str = None, llm=None, now=None) -> dict:
    now = now or data.now_ist()
    user = circle.STORE.user(user_id)
    parsed = intake.parse(text, names=guardrails.personal_names(user), llm=llm)
    ta = (parsed.get("lang") == "ta") or (lang == "ta" and parsed.get("lang") != "en")
    steps = [_step(_t("understood_ta" if parsed.get("lang") == "ta" else "understood", False))]
    ctx = {"user_id": user_id, "user": user, "parsed": parsed, "ta": ta, "steps": steps, "channel": channel,
           "user_phone": user_phone, "now": now}

    handler = HANDLERS.get(parsed["intent"], _unknown)
    if parsed.get("fallback"):
        handler = _unknown
    result = handler(ctx)

    guardrails.anonymous_log({
        "intent": parsed["intent"], "from_area": parsed.get("from") and route.match_place(parsed["from"]),
        "to_area": parsed.get("to") and route.match_place(parsed["to"]), "hour": now.hour,
        "mode": (result.get("card") or {}).get("mode"), "lang": parsed.get("lang"), "channel": channel,
        "route_found": (result.get("card") or {}).get("type") == "route",
        "safe_place_found": bool(((result.get("card") or {}).get("option") or {}).get("safe_wait")),
    })
    public_intake = {k: v for k, v in parsed.items() if k not in ("raw_text",)}
    return {
        "reply": {"text": result["text"], "lang": "ta" if ta else "en"},
        "card": result.get("card"),
        "actions": result.get("actions", []),
        "steps": steps,
        "agent_steps": steps,  # same list, the name the n8n workflow reads
        "fallback": (result.get("card") or {}).get("type") == "fallback",
        "aval_state": result.get("aval_state", "talking"),
        "sms_text": guardrails.clamp_sms(result.get("sms") or result["text"], tamil=False),
        "intake": public_intake,
        "sample_data": True,
    }


# ---------- handlers ----------

def _plan_trip(ctx, intent_hint=None):
    p, ta, steps = ctx["parsed"], ctx["ta"], ctx["steps"]
    frm = p.get("from") or DEFAULT_START
    to = p.get("to")
    if not to:
        return {"text": _t("where_to", ta), "aval_state": "idle"}
    plan = route.plan(frm, to, p.get("time"), p.get("with_child", False))
    if plan.get("error") or not plan["options"]:
        return {"text": _t("no_route", ta), "aval_state": "idle",
                "card": {"type": "no_route", "unmatched": plan.get("unmatched", []), "not_running_now": plan.get("not_running_now", [])}}
    minutes = data.to_minutes(plan["time"])
    ranked = safety.rank_options(plan["options"], minutes, "safest", p.get("with_child", False))
    best = ranked[0]
    used = {l["mode"] for o in ranked for l in o["legs"]}
    kinds = [m for m in ("bus", "metro", "train", "auto") if m in used]
    steps.append(_step("Compared " + ", ".join(kinds[:-1]) + (" and " if len(kinds) > 1 else "") + kinds[-1]))
    steps.append(_step(f"Ranked {best.get('safe_places_ranked', 0)} safe places near the stop"))
    watchers = [c for c in ctx["user"]["contacts"] if c.get("accepted")]
    if watchers:
        steps.append(_step(f"{watchers[0]['label']} will get your trip when you start", "pending"))
    _session(ctx["user_id"])["last_plan"] = {"from": plan["from"], "to": plan["to"], "time": plan["time"], "option": best}

    if best["kind"] == "auto":
        stopped = ", ".join(plan.get("not_running_now", [])) or "Buses"
        text = f"{stopped} have stopped for now. Auto is about Rs {best['fare_inr']}, {best['total_min']} min (estimate)."
        if ta:
            text = f"இப்போது பஸ் இல்லை. ஆட்டோ சுமார் ₹{best['fare_inr']}, {best['total_min']} நிமிடம்."
        sms = f"No bus now. Auto ~Rs {best['fare_inr']}, {best['total_min']} min. Book in Namma Yatri or Rapido. Reply HELP anytime"
        return {"text": text, "sms": sms, "aval_state": "talking",
                "actions": [{"id": "start_trip", "label": "Start trip", "label_ta": "பயணம் தொடங்கு",
                             "payload": {"from": plan["from"], "to": plan["to"], "time": plan["time"], "option_id": best["id"]}}],
                "card": {"type": "route", "mode": "auto", "from": plan["from"], "to": plan["to"], "time": plan["time"],
                         "with_child": p.get("with_child", False), "option": best, "alternatives": ranked[1:],
                         "not_running_now": plan.get("not_running_now", []), "source": "sample"}}
    transit = [l for l in best["legs"] if l["mode"] != "walk"]
    first = transit[0]
    # never claim a specific bus is free: the scheme covers ordinary (white-board) buses only
    free = f". {FREE_TEXT}" if best["is_free"] else f" costs Rs {best['fare_inr']}"
    nxt = f", next at {_hm(best['next'][0])}" if best["next"] else ""
    child = " Good with your child: no switches." if p.get("with_child") and best["switches"] == 0 else ""
    text = f"Here's your safest way. {first['label']}{free}{nxt}. You'll reach by {_hm(best['reach_by'])}.{child}"
    if ta:
        wait = best["safe_wait"]["name_ta"] if best.get("safe_wait") else ""
        text = f"{first['label']} {FREE_TEXT_TA if best['is_free'] else '₹' + str(best['fare_inr'])}" \
               f"{' · ' + _hm(best['next'][0]) if best['next'] else ''}" \
               f"{' · ' + wait + '-ல் காத்திருங்கள்' if wait else ''} · {_hm(best['reach_by'])}-க்குள் சேருவீர்கள்"
    sw = best.get("safe_wait")
    sms = f"{first['label'].upper() if first['mode'] != 'bus' else 'BUS ' + first['label']} at {best.get('board_at') or plan['from']}\n" \
          f"Next ~{_hm(best['next'][0]) if best['next'] else '-'}. {FREE_SMS if best['is_free'] else 'Rs ' + str(best['fare_inr']) + '.'}" + (f" Safe wait: {sw['name']}" + (f" {sw['distance_m']}m" if sw.get("distance_m") else "") if sw else "") + "\nReply START when you board"
    alt = next((o for o in ranked[1:] if o["kind"] != best["kind"]), None)
    actions = [{"id": "start_trip", "label": "Start trip", "label_ta": "பயணம் தொடங்கு",
                "payload": {"from": plan["from"], "to": plan["to"], "time": plan["time"], "option_id": best["id"]}}]
    if alt:
        actions.append({"id": "choose_option", "label": f"{'Metro' if 'metro' in alt['kind'] else alt['kind'].title()} instead",
                        "label_ta": "வேறு வழி", "payload": {"from": plan["from"], "to": plan["to"], "time": plan["time"], "option_id": alt["id"]}})
    return {"text": text, "sms": sms, "aval_state": "talking", "actions": actions,
            "card": {"type": "route", "mode": best["kind"], "from": plan["from"], "to": plan["to"], "time": plan["time"],
                     "with_child": p.get("with_child", False), "option": best, "alternatives": ranked[1:], "source": "sample"}}


def _free_bus(ctx):
    p = ctx["parsed"]
    if p.get("to"):
        return _plan_trip(ctx)
    stop = p.get("from") or DEFAULT_START
    arr = route.arrivals(stop, p.get("time"), free_only=True)
    ctx["steps"].append(_step(f"Checked free buses at {arr.get('stop', stop)}"))
    if not arr.get("arrivals"):
        return {"text": "No bus in the timetable right now.", "card": {"type": "arrivals", **arr}}
    a = arr["arrivals"][0]
    text = f"Bus {a['number']} to {a['towards']} in {a['in_min']} min ({_hm(a['time'])}). {FREE_TEXT}"
    if ctx["ta"]:
        text = f"பஸ் {a['number']} · {a['in_min']} நிமிடத்தில் ({a['time']}). {FREE_TEXT_TA}"
    return {"text": text, "card": {"type": "arrivals", "mode": "bus", **arr}}


def _safe_route_home(ctx):
    p, user = ctx["parsed"], ctx["user"]
    trip = circle.find_active_trip(ctx["user_id"])
    area = p.get("to") or (trip and trip["to"]) or user.get("home_area") or "Nungambakkam"
    area = route.match_place(area) or area
    code = (trip and trip.get("alight_code")) or _stop_code_for(area)
    minutes = data.parse_time(p.get("time"))
    result = safety.compare_walk_paths(code or "", minutes, user["contacts"])
    if not result["paths"]:
        return {"text": _t("no_route", ctx["ta"]), "card": {"type": "no_route"}}
    best = result["paths"][0]
    ctx["steps"].append(_step(f"Compared {len(result['paths'])} ways from the stop: people around, open shops, your people"))
    near = best["your_people"][0]["label"] if best["your_people"] else None
    text = f"Walk the {best['name'].lower()}: {best['people_label'].lower()}, {best['shops_open']} shops open" + (f", {near} is near." if near else ".")
    if ctx["ta"]:
        text = f"{best['name_ta']} வழியாக நடங்கள்: {best['people_label_ta']}, {best['shops_open']} கடைகள் திறந்துள்ளன" + (f", {near} அருகில்." if near else ".")
    actions = [{"id": "walk", "label": f"Walk {best['name'].lower()}", "label_ta": "இந்த வழியில் நட", "payload": {"path_id": best["id"]}}]
    if near:
        actions.append({"id": "ask_to_meet", "label": f"Ask {near} to meet", "label_ta": f"{near}-ஐ சந்திக்கக் கேள்",
                        "payload": {"contact_id": best["your_people"][0]["id"]}, "needs_confirmation": True})
    return {"text": text, "actions": actions, "card": {"type": "safe_route", "mode": "walk", "area": area, **result}}


def _places_open(ctx):
    p = ctx["parsed"]
    area = route.match_place(p.get("from") or p.get("to") or "") if (p.get("from") or p.get("to")) else None
    coords = data.area_coords(area) if area else None
    res = places.search(lat=coords[0] if coords else None, lng=coords[1] if coords else None,
                        open_now=True, type=p.get("place_type"), time=p.get("time"))
    ctx["steps"].append(_step(f"Found {res['count']} places open now" + (f" near {area}" if area else "")))
    if not res["places"]:
        return {"text": "Nothing open nearby in the sample data right now.", "card": {"type": "places", **res}}
    top = res["places"][0]
    text = f"{res['count']} places open now. Nearest safe one: {top['name']}, {top.get('distance_m', 0)} m."
    if ctx["ta"]:
        text = f"இப்போது {res['count']} இடங்கள் திறந்துள்ளன. அருகில்: {top.get('name_ta') or top['name']}"
    return {"text": text, "card": {"type": "places", **res}}


def _place_details(ctx):
    pid = ctx["parsed"].get("place_name")
    d = places.details(pid) if pid else {"error": "not_found"}
    if d.get("error"):
        return _unknown(ctx)
    ctx["steps"].append(_step(f"Checked {d['name']}: hours, reviews, safety at night"))
    status = "open now" if d["open_now"] else "closed now"
    text = f"{d['name']} is {status}. Safety at night: {d['night_safety']['label']}. Rated {d['rating']} by {d['reviews_count']} women."
    return {"text": text, "card": {"type": "place", "place": d}}


def _book_ticket(ctx):
    p = ctx["parsed"]
    last = _session(ctx["user_id"]).get("last_plan")
    if p.get("to"):
        res = _plan_trip(ctx)
        last = _session(ctx["user_id"]).get("last_plan")
        if not last:
            return res
    if not last:
        return {"text": _t("no_trip", ctx["ta"])}
    plan = route.plan(last["from"], last["to"], last["time"])
    payable = [o for o in plan["options"] if o["kind"] != "auto" and o["fare_inr"] > 0]
    if not payable:
        return {"text": f"No ticket needed on ordinary buses. {FREE_TEXT} Deluxe / AC buses need a ticket.", "card": {"type": "info"}}
    opt = payable[0]
    order = pay.create_order(opt, plan["from"], plan["to"], confirmed=False)
    ctx["steps"].append(_step(f"Prepared a Rs {opt['fare_inr']} test ticket - waiting for your OK", "pending"))
    return {"text": order["preview"], "aval_state": "talking",
            "card": {"type": "confirm", "action": "pay", "summary": order["summary"]},
            "actions": [{"id": "pay", "label": "Yes, pay", "label_ta": "ஆம், செலுத்து", "needs_confirmation": True,
                         "payload": {"from": plan["from"], "to": plan["to"], "time": plan["time"], "option_id": opt["id"]}},
                        {"id": "cancel", "label": "No", "label_ta": "வேண்டாம்"}]}


def _share_trip(ctx):
    last = _session(ctx["user_id"]).get("last_plan")
    watchers = [c for c in ctx["user"]["contacts"] if c.get("accepted")]
    if not last or not watchers:
        return {"text": _t("no_trip", ctx["ta"]) if not last else "Add someone to your circle first."}
    who = watchers[0]["label"]
    ctx["steps"].append(_step(f"Ready to send your trip to {who} - waiting for your OK", "pending"))
    return {"text": f"Send your trip to {who}?", "card": {"type": "confirm", "action": "share_trip"},
            "actions": [{"id": "start_trip", "label": f"Yes, send to {who}", "needs_confirmation": True,
                         "payload": {"from": last["from"], "to": last["to"], "time": last["time"],
                                     "option_id": last["option"]["id"], "confirmed": True}},
                        {"id": "cancel", "label": "No"}]}


def _start_trip(ctx):
    last = _session(ctx["user_id"]).get("last_plan")
    if not last:
        return {"text": _t("no_trip", ctx["ta"])}
    if ctx["channel"] == "sms":
        # START is an explicit command. No message to the circle now; Journey Watch alerts only if she doesn't reach.
        res = circle.start_trip(ctx["user_id"], last["option"], last["from"], last["to"], notify_circle=False,
                                user_phone=ctx["user_phone"], now=ctx["now"])
        ctx["steps"].append(_step("Journey Watch is on"))
        eta = res["trip"]["eta_hhmm"]
        return {"text": f"Journey Watch ON. ETA {eta}. Reply REACHED when you arrive. Reply HELP anytime.",
                "card": {"type": "trip", "trip": res["trip"]}, "aval_state": "talking"}
    return _share_trip(ctx) if any(c.get("accepted") for c in ctx["user"]["contacts"]) else {
        "text": "Tap Start trip to begin Journey Watch.",
        "actions": [{"id": "start_trip", "label": "Start trip", "payload": {"from": last["from"], "to": last["to"],
                     "time": last["time"], "option_id": last["option"]["id"]}}]}


def _reached(ctx):
    trip = circle.find_active_trip(ctx["user_id"])
    if not trip:
        return {"text": "No active trip. Glad you're safe!", "aval_state": "cheer"}
    res = circle.reached(trip["trip_id"], now=ctx["now"])
    ctx["steps"].append(_step("Marked your trip as reached"))
    d = res["delivery"]
    told = " Your circle was told." if d["sent"] else (" (Demo: circle message logged, not sent.)" if d["demo_logged"] else "")
    return {"text": f"Great, you reached safely.{told}", "aval_state": "cheer", "card": {"type": "trip", "trip": res["trip"]}}


def _check_in(ctx):
    trip = circle.find_active_trip(ctx["user_id"])
    if not trip:
        return {"text": "No active trip right now."}
    res = circle.checkin(trip["trip_id"], ok=True, now=ctx["now"])
    ctx["steps"].append(_step("Checked in"))
    return {"text": "Thanks, noted that you're okay.", "card": {"type": "trip", "trip": res["trip"]}}


def _stop(ctx):
    trip = circle.find_active_trip(ctx["user_id"])
    if trip:
        trip["status"] = "stopped"
        trip["last_location"] = None
    return {"text": "Journey Watch stopped."}


def _sos(ctx):
    res = circle.sos(ctx["user_id"], now=ctx["now"])
    d = res["delivery"]
    if d["sent"]:
        told = f"Your circle is informed ({d['sent']})."
        ctx["steps"].append(_step(f"Alerted {d['sent']} people in your circle"))
    elif d["demo_logged"]:
        told = "Demo mode: alert logged, not sent as SMS."
        ctx["steps"].append(_step("Demo mode: circle alert logged, not sent", "warn"))
    else:
        told = "Could not reach your circle."
        ctx["steps"].append(_step("Could not reach your circle", "warn"))
    text = f"Women helpline 181. Police 100. {told}"
    if ctx["ta"]:
        text = f"பெண்கள் உதவி 181. காவல் 100. {told}"
    return {"text": text, "sms": f"Women helpline 181. Police 100. {told}", "aval_state": "alert",
            "card": {"type": "sos", **res}}


def _call_me(ctx):
    """CALL: AVAL phones her back (Twilio) and talks in Tamil. Falls back to SMS honestly."""
    from .agents import callback
    if ctx["channel"] != "sms" or not ctx["user_phone"]:
        return {"text": "Tap the mic to talk to AVAL here. CALL works from SMS.", "aval_state": "idle"}
    res = callback.start(ctx["user_phone"], lang="ta" if ctx["ta"] or ctx["parsed"].get("lang") != "en" else "en")
    if res["status"] == "calling":
        ctx["steps"].append(_step("Calling you back now"))
        return {"text": "Calling you now from SafePath. Answer to talk to AVAL.", "card": {"type": "call", **res}}
    ctx["steps"].append(_step("Call-back not available right now", "warn"))
    return {"text": "Call-back is not available right now. Send your trip by SMS. Eg: Nungambakkam bus",
            "card": {"type": "call", **res}}


def _help(ctx):
    return {"text": _t("help", ctx["ta"]), "aval_state": "idle"}


def _unknown(ctx):
    return {"text": _t("fallback", ctx["ta"]), "sms": intake.FALLBACK_REPLY, "aval_state": "idle",
            "card": {"type": "fallback"}}


HANDLERS = {
    "plan_trip": _plan_trip, "free_bus_now": _free_bus, "safe_route_home": _safe_route_home,
    "places_open_now": _places_open, "place_details": _place_details, "book_ticket": _book_ticket,
    "share_trip": _share_trip, "start_trip": _start_trip, "reached": _reached, "check_in": _check_in,
    "stop": _stop, "sos": _sos, "help": _help, "call_me": _call_me, "unknown": _unknown,
}
