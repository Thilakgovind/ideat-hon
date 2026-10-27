"""Loads the sample data files and shared helpers (time, distance, crowd)."""
import json
import math
from datetime import datetime, timedelta, timezone

from .config import DATA_DIR

IST = timezone(timedelta(hours=5, minutes=30))
CROWD_ORDER = ["empty", "quiet", "moderate", "busy"]


_CACHE: dict = {}
SOURCE: dict = {}  # name -> "json" | "supabase"


def load(name: str) -> dict:
    """Dataset by name. /data JSON by default; replaced by Supabase rows when the store loads them."""
    if name not in _CACHE:
        with open(DATA_DIR / f"{name}.json", encoding="utf-8") as f:
            _CACHE[name] = json.load(f)
        SOURCE[name] = "json"
    return _CACHE[name]


def override(name: str, obj: dict, source: str = "supabase"):
    _CACHE[name] = obj
    SOURCE[name] = source


def reset():
    """Back to the /data JSON files (tests, or when Supabase becomes unreachable)."""
    _CACHE.clear()
    SOURCE.clear()


def routes():
    return load("routes")["routes"]


def metro():
    return load("metro")


def trains():
    return load("trains")["lines"]


def transfers():
    return load("transfers")["transfers"]


def areas():
    return load("areas")["areas"]


def places():
    return load("places")["places"]


def walk_paths():
    return load("walk_paths")["paths"]


def circle_seed():
    return load("circle")


# ---------- time ----------

def now_ist() -> datetime:
    return datetime.now(IST)


def to_minutes(hhmm: str) -> int:
    h, m = hhmm.strip().split(":")
    return int(h) * 60 + int(m)


def fmt_minutes(total: int) -> str:
    total %= 24 * 60
    return f"{total // 60:02d}:{total % 60:02d}"


def parse_time(value) -> int:
    """'HH:MM' / 'now' / None -> minutes since midnight (IST)."""
    if value and value != "now":
        try:
            return to_minutes(value)
        except (ValueError, AttributeError):
            pass
    n = now_ist()
    return n.hour * 60 + n.minute


# ---------- geo ----------

def haversine_m(lat1, lng1, lat2, lng2) -> float:
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def area_coords(name: str):
    """Area centre, or a stop's own coordinates when the name is a stop."""
    n = (name or "").lower()
    for a in areas():
        if a["name"].lower() == n:
            return a["lat"], a["lng"]
    for r in routes():
        for s in r["stops"]:
            if s["name"].lower() == n and "lat" in s:
                return s["lat"], s["lng"]
    return None


def stop_name(code: str):
    """Stop / station name for a code, from the bus, metro and train data."""
    lines = [r["stops"] for r in routes()] + [l["stations"] for l in metro()["lines"]] + [l["stations"] for l in trains()]
    for stops in lines:
        for s in stops:
            if s["code"] == code:
                return s["name"]
    return None


def area_ta(name: str) -> str:
    for a in areas():
        if a["name"] == name:
            return a.get("name_ta", name)
    return name


# ---------- crowd ----------

def crowd_at(crowd_by_hour: dict, minutes: int) -> str:
    """Crowd level for the most recent defined hour at or before `minutes`."""
    if not crowd_by_hour:
        return "quiet"
    hour = (minutes // 60) % 24
    keys = sorted(int(k) for k in crowd_by_hour)
    earlier = [k for k in keys if k <= hour]
    key = earlier[-1] if earlier else keys[-1]
    return crowd_by_hour[f"{key:02d}"]
