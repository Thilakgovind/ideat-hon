"""Places agent: places near a point or along a route, open now, reviews."""
from .. import data
from . import safety

DEFAULT_POINT = (13.0878, 80.2006)  # Anna Nagar West bus stop (demo start)

# Explore screen chips -> filters
CHIPS = {
    "open_night": {"open_at": 21 * 60},
    "women_run": {"women_run": True},
    "pharmacy": {"types": {"pharmacy"}},
    "food": {"types": {"tea_shop", "bakery", "shg_kiosk"}},
    "transit": {"types": {"bus_shelter"}},
    "help": {"types": {"police_booth", "hospital"}},
}


def _summary(p, minutes, origin=None):
    out = {
        "id": p["id"], "name": p["name"], "name_ta": p.get("name_ta"), "type": p["type"], "category": p["category"],
        "address": p["address"], "near_stop": p["near_stop"], "lat": p["lat"], "lng": p["lng"],
        "open_now": safety.is_open(p, minutes), "open_24h": p.get("open_24h", False),
        "open": p["open"], "close": p["close"],
        "women_run": p.get("women_run", False), "well_lit": p.get("well_lit", False),
        "crowd_now": data.crowd_at(p.get("crowd_by_hour", {}), minutes),
        "rating": p.get("rating"), "reviews_count": p.get("reviews_count", 0), "photo": p.get("photo"),
        "safety_score": safety.place_score(p, minutes), "source": p.get("source", "sample"),
    }
    if origin:
        out["distance_m"] = int(round(data.haversine_m(origin[0], origin[1], p["lat"], p["lng"])))
    return out


def search(lat=None, lng=None, radius_m=2000, open_now=False, type=None, chip=None,
           women_run=None, well_lit=None, route_stops=None, time=None) -> dict:
    minutes = data.parse_time(time)
    origin = (lat, lng) if lat is not None and lng is not None else DEFAULT_POINT
    rules = dict(CHIPS.get(chip, {}))
    types = set(type.split(",")) if type else rules.get("types")
    out = []
    for p in data.places():
        if route_stops is not None:
            if p["near_stop"] not in route_stops:
                continue
        elif data.haversine_m(origin[0], origin[1], p["lat"], p["lng"]) > radius_m:
            continue
        if types and p["type"] not in types:
            continue
        if open_now and not safety.is_open(p, minutes):
            continue
        if "open_at" in rules and not safety.is_open(p, rules["open_at"]):
            continue
        if (women_run or rules.get("women_run")) and not p.get("women_run"):
            continue
        if well_lit and not p.get("well_lit"):
            continue
        out.append(_summary(p, minutes, origin if route_stops is None else None))
    out.sort(key=lambda x: (-x["safety_score"], x.get("distance_m", 0)))
    types_count = {}
    for p in out:
        types_count[p["type"]] = types_count.get(p["type"], 0) + 1
    return {"count": len(out), "open_now_count": sum(p["open_now"] for p in out), "types": types_count,
            "time": data.fmt_minutes(minutes), "center": {"lat": origin[0], "lng": origin[1]},
            "places": out, "source": "sample"}


def along_route(option: dict, time=None) -> dict:
    stops = {l.get(k) for l in option.get("legs", []) for k in ("from_code", "to_code") if l.get(k)}
    return search(route_stops=stops, time=time)


def details(place_id: str, time=None, origin=None) -> dict:
    minutes = data.parse_time(time)
    for p in data.places():
        if p["id"] == place_id:
            out = _summary(p, minutes, origin or DEFAULT_POINT)
            out["reviews"] = p.get("reviews", [])
            out["night_safety"] = safety.night_safety(p)
            out["can_wait_inside"] = p.get("can_wait_inside", False)
            out["closes_label"] = "Open 24 hours" if p.get("open_24h") else f"Closes {safety._ampm(p['close'])}"
            return out
    return {"error": "not_found", "id": place_id}


GENERIC_WORDS = {"the", "shop", "stall", "store", "stores", "near", "road", "high", "h", "24"}


def _area_words():
    import re
    names = [a["name"] for a in data.areas()] + [x for a in data.areas() for x in a.get("aliases", [])]
    return {w for n in names for w in re.findall(r"[a-z0-9]+", n.lower())}


def find_by_name(text: str):
    """Place id whose name best overlaps the text. Needs a distinctive word
    (not an area name like 'Anna Nagar', not a generic word like 'shop')."""
    import re
    words = set(re.findall(r"[a-z0-9]+", (text or "").lower()))
    skip = _area_words() | GENERIC_WORDS
    best, best_score = None, 0.0
    for p in data.places():
        if p.get("name_ta") and p["name_ta"] in (text or ""):
            return p["id"]
        tokens = re.findall(r"[a-z0-9]+", p["name"].lower())
        distinctive = [t for t in tokens if t not in skip]
        if not distinctive or distinctive[0] not in words:
            continue
        score = sum(t in words for t in tokens) / len(tokens)
        if score > best_score:
            best, best_score = p["id"], score
    return best if best_score >= 0.5 else None
