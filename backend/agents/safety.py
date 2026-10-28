"""Safety agent: ranks places, routes and walking paths with neutral signals only.

Signals used: open now, open 24h, women-run / SHG, well lit, crowd level
(anonymous area level), switches, and whether trusted contacts are near.
Never: who the people are (no profiling by caste, religion, class, etc.).
"""
from .. import data

NEUTRAL_SIGNALS = ("open", "close", "open_24h", "women_run", "well_lit", "can_wait_inside", "crowd_by_hour")
NEAR_PATH_M = 150
PEOPLE_LABEL = {"busy": "Busy", "moderate": "Some people", "quiet": "Quiet", "empty": "Empty"}
PEOPLE_LABEL_TA = {"busy": "கூட்டம் உண்டு", "moderate": "சிலர் உள்ளனர்", "quiet": "அமைதி", "empty": "யாரும் இல்லை"}


# ---------- places ----------

def is_open(place: dict, minutes: int) -> bool:
    if place.get("open_24h"):
        return True
    o, c = data.to_minutes(place["open"]), data.to_minutes(place["close"])
    m = minutes % (24 * 60)
    return o <= m < c if o <= c else (m >= o or m < c)


def place_score(place: dict, minutes: int) -> int:
    """Brief §5: open now +3, 24h +1, women-run +2, well lit +2 after 6pm,
    busy/moderate +2, empty -2 after 7pm."""
    p = {k: place.get(k) for k in NEUTRAL_SIGNALS}  # only neutral fields are ever read
    score = 0
    if is_open(place, minutes):
        score += 3
    if p["open_24h"]:
        score += 1
    if p["women_run"]:
        score += 2
    if p["well_lit"] and minutes >= 18 * 60:
        score += 2
    crowd = data.crowd_at(p["crowd_by_hour"] or {}, minutes)
    if crowd in ("busy", "moderate"):
        score += 2
    elif crowd == "empty" and minutes >= 19 * 60:
        score -= 2
    return score


def rank_places(places: list, minutes: int) -> list:
    ranked = []
    for p in places:
        ranked.append({**p, "open_now": is_open(p, minutes), "crowd_now": data.crowd_at(p.get("crowd_by_hour", {}), minutes),
                       "safety_score": place_score(p, minutes)})
    ranked.sort(key=lambda x: (-x["safety_score"], x["type"] != "shg_kiosk", x["name"]))
    return ranked


def night_safety(place: dict) -> dict:
    """'Safety at night' card for the Place screen (evaluated at 9 pm)."""
    nine_pm = 21 * 60
    tags, points = [], 0
    if place.get("women_run"):
        tags.append("Women-run"); points += 1
    if place.get("well_lit"):
        tags.append("Well-lit"); points += 1
    crowd = data.crowd_at(place.get("crowd_by_hour", {}), nine_pm)
    if crowd in ("busy", "moderate"):
        close = "24 h" if place.get("open_24h") else _ampm(place["close"])
        tags.append(f"Busy till {close}" if crowd == "busy" else f"Some people till {close}"); points += 1
    if place.get("can_wait_inside"):
        tags.append("Can wait inside"); points += 1
    if is_open(place, 22 * 60):
        points += 1
    label = "Very good" if points >= 4 else "Good" if points == 3 else "Okay" if points == 2 else "Low"
    return {"label": label, "tags": tags, "evaluated_at": "21:00", "signals": "neutral only"}


def _ampm(hhmm):
    m = data.to_minutes(hhmm)
    h = m // 60
    suffix = "am" if h < 12 else "pm"
    h = h % 12 or 12
    return f"{h}:{m % 60:02d} {suffix}" if m % 60 else f"{h} {suffix}"


NEAR_STOP_M = 900


def places_near_stop(code: str) -> list:
    """Places tagged with this stop; for real (GTFS) stops, places within NEAR_STOP_M, with distance."""
    tagged = [p for p in data.places() if p.get("near_stop") == code]
    at = None if tagged else data.stop_coords(code)
    if not at:
        return tagged
    near = []
    for p in data.places():
        d = data.haversine_m(at[0], at[1], p["lat"], p["lng"])
        if d <= NEAR_STOP_M:
            near.append({**p, "distance_m": round(d)})
    return sorted(near, key=lambda p: p["distance_m"])


# ---------- routes ----------

def score_option(opt: dict, minutes: int, with_child: bool = False) -> dict:
    """Adds safety_score (0-100), tags and safe_wait to a route option."""
    night = minutes >= 19 * 60 or minutes < 6 * 60
    score, tags = 50, []
    board = rank_places(places_near_stop(opt.get("board_code") or ""), minutes)
    alight = rank_places(places_near_stop(opt.get("alight_code") or ""), minutes)
    open_board = [p for p in board if p["open_now"]]
    safe_wait = open_board[0] if open_board else None

    if opt["kind"] == "auto":
        score += 5 if not night else -5
        tags.append("Door to door")
    else:
        score += min(15, 5 * len(open_board)) + min(10, 3 * len([p for p in alight if p["open_now"]]))
        bus_legs = [l for l in opt["legs"] if l["mode"] == "bus"]
        if bus_legs and all(l.get("stops_well_lit") for l in bus_legs):
            score += 10
        crowd = [p["crowd_now"] for p in open_board]
        if any(c == "busy" for c in crowd) and any(l.get("stops_well_lit") for l in bus_legs):
            tags.append("Busy, well-lit stops")
        if opt["switches"] == 0:
            score += 10
            tags.append("No switches")
        else:
            sw = opt.get("switch_info", {})
            score += 3 if sw.get("lit") else -10
            score -= 5 * opt["switches"] * (2 if with_child else 1)
        if safe_wait:
            kind = "SHG kiosk" if safe_wait["type"] == "shg_kiosk" else safe_wait["category"]
            tags.insert(0, f"Safe wait: {kind}")
            if safe_wait.get("women_run"):
                score += 5
        walk = sum(l["minutes"] for l in opt["legs"] if l["mode"] == "walk")
        if night:
            score -= walk
    opt = dict(opt)
    opt["safety_score"] = max(0, min(100, score))
    opt["safety_tags"] = tags
    opt["safe_wait"] = _brief_place(safe_wait) if safe_wait else None
    opt["safe_places_ranked"] = len(board)
    return opt


def _brief_place(p):
    return {"id": p["id"], "name": p["name"], "name_ta": p.get("name_ta"), "type": p["type"],
            "women_run": p.get("women_run", False), "open_now": p["open_now"], "close": p.get("close"),
            "open_24h": p.get("open_24h", False), "location": p.get("address"), "crowd_now": p["crowd_now"],
            **({"distance_m": p["distance_m"]} if p.get("distance_m") is not None else {})}


def _reach(o):
    """Minutes from the asked time to arrival (handles a trip that crosses midnight)."""
    return o["total_min"] + o.get("wait_min", 0)


def rank_options(options: list, minutes: int, sort: str = "safest", with_child: bool = False) -> list:
    scored = [score_option(o, minutes, with_child) for o in options]
    keys = {
        # equal safety: the one that gets her there first (real timetables have real waits)
        "safest": lambda o: (-o["safety_score"], _reach(o), o["total_min"]),
        "cheapest": lambda o: (o["fare_inr"], -o["safety_score"]),
        "fastest": lambda o: (o["total_min"], -o["safety_score"]),
    }
    scored.sort(key=keys.get(sort, keys["safest"]))
    if scored:
        best_safe = max(scored, key=lambda o: o["safety_score"])
        fastest = min(scored, key=lambda o: o["total_min"])
        cheapest = min(scored, key=lambda o: o["fare_inr"])
        for o in scored:
            o["badges"] = [b for b, x in (("SAFEST", best_safe), ("FASTEST", fastest), ("CHEAPEST", cheapest)) if o is x]
    return scored


# ---------- walking paths (Safe way home) ----------

def _distance_to_path(lat, lng, polyline):
    """Metres from a point to the nearest segment of a polyline (flat-earth approx, fine at street scale)."""
    import math
    kx = 111320 * math.cos(math.radians(lat))
    ky = 110540
    best = float("inf")
    for (a_lat, a_lng), (b_lat, b_lng) in zip(polyline, polyline[1:]):
        ax, ay = (a_lng - lng) * kx, (a_lat - lat) * ky
        bx, by = (b_lng - lng) * kx, (b_lat - lat) * ky
        dx, dy = bx - ax, by - ay
        t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(ax + t * dx, ay + t * dy))
    return best


def compare_walk_paths(stop_code: str, minutes: int, contacts=()) -> dict:
    """Compare walking paths from a stop: people around, shops open, your people."""
    paths = [p for p in data.walk_paths() if p["stop"] == stop_code]
    by_id = {p["id"]: p for p in data.places()}
    results = []
    for path in paths:
        crowd = data.crowd_at(path["crowd_by_hour"], minutes)
        shops = [by_id[i] for i in path["place_ids"] if i in by_id]
        open_shops = [s for s in shops if is_open(s, minutes)]
        people = []
        for c in contacts:
            if not c.get("accepted") or c.get("lat") is None or c.get("status") == "at_home":
                continue
            d = _distance_to_path(c["lat"], c["lng"], path["polyline"])
            if d <= NEAR_PATH_M:
                people.append({"id": c["id"], "label": c["label"], "off_route_m": int(round(d / 10.0) * 10),
                               "status": c.get("status"), "lat": c["lat"], "lng": c["lng"]})
        score = {"busy": 30, "moderate": 20, "quiet": 5, "empty": -10}[crowd]
        score += 8 * len(open_shops) + (15 if path["well_lit"] else -10) + 10 * len(people)
        results.append({
            "id": path["id"], "name": path["name"], "name_ta": path["name_ta"],
            "minutes": path["minutes"], "distance_m": path["distance_m"], "well_lit": path["well_lit"],
            "people_around": crowd, "people_label": PEOPLE_LABEL[crowd], "people_label_ta": PEOPLE_LABEL_TA[crowd],
            "shops_open": len(open_shops),
            "open_shop_names": [("%s (24 h)" % s["category"].split(" (")[0]) if s.get("open_24h") else s["name"] for s in open_shops],
            "open_shops": [{"id": s["id"], "name": s["name"], "type": s["type"], "lat": s["lat"], "lng": s["lng"]} for s in open_shops],
            "closed_shops": [{"id": s["id"], "name": s["name"], "lat": s["lat"], "lng": s["lng"]} for s in shops if s not in open_shops],
            "your_people": people,
            "polyline": path["polyline"],
            "score": score,
            "source": path.get("source", "sample"),
        })
    results.sort(key=lambda r: -r["score"])
    if results:
        results[0]["badge"] = "SAFEST"
    at_home = [{"id": c["id"], "label": c["label"], "status": "at_home", "lat": c.get("lat"), "lng": c.get("lng")}
               for c in contacts if c.get("accepted") and c.get("status") == "at_home"]
    return {"stop_code": stop_code, "time": data.fmt_minutes(minutes), "paths": results, "at_destination": at_home,
            "note": "Crowd shown as anonymous areas, never individuals", "source": "sample"}
