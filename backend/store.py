"""Storage: Supabase when it is configured and reachable, otherwise in-memory + /data JSON.

- Reads: places, reviews, stops, routes, transfers are loaded from Supabase into the same
  structures the agents already use (data.override), so ranking logic is unchanged.
- Writes: trips, trip_events, circle_contacts, users and the anonymous request_log are
  mirrored to Supabase in a background thread. A failed write never breaks a request.
- Uses the service key (backend only). Nothing here prints keys or row data.
"""
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import httpx

from . import config, data

TIMEOUT = 10
PROBE_TTL = 300
STATUS = {"mode": "memory", "reason": "not checked", "loaded": {}, "writes_ok": 0, "writes_failed": 0, "checked_at": 0}
_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="supabase")
_lock = threading.Lock()


def _rest():
    key = config.env("SUPABASE_SERVICE_KEY")
    return config.env("SUPABASE_URL").rstrip("/") + "/rest/v1", {"apikey": key, "Authorization": f"Bearer {key}"}


def configured() -> bool:
    return config.has("supabase")


def available(force: bool = False) -> bool:
    """True when the service key works and the SafePath tables are visible (cached for 5 min)."""
    if not configured():
        STATUS.update(mode="memory", reason="SUPABASE_URL / SUPABASE_SERVICE_KEY missing")
        return False
    if not force and time.time() - STATUS["checked_at"] < PROBE_TTL:
        return STATUS["mode"] == "supabase"
    base, h = _rest()
    try:
        r = httpx.get(f"{base}/places", params={"select": "id", "limit": 1}, headers=h, timeout=TIMEOUT)
        ok = r.status_code == 200
        reason = "" if ok else ("tables not visible to the API (run migrations)" if r.status_code == 404 else f"HTTP {r.status_code}")
    except httpx.HTTPError as e:
        ok, reason = False, type(e).__name__
    STATUS.update(mode="supabase" if ok else "memory", reason=reason or "ok", checked_at=time.time())
    return ok


def _get(table, params=None):
    base, h = _rest()
    rows, start = [], 0
    while True:
        r = httpx.get(f"{base}/{table}", params={"select": "*", **(params or {})},
                      headers={**h, "Range": f"{start}-{start + 999}"}, timeout=TIMEOUT)
        r.raise_for_status()
        page = r.json()
        rows += page
        if len(page) < 1000:
            return rows
        start += 1000


def _hm(t):
    return (t or "00:00")[:5]


# ---------------------------------------------------------------- reads

def load_public() -> dict:
    """Pull public tables into data.* (same shapes as /data). Returns counts loaded."""
    if not available():
        return {}
    try:
        stops = {s["id"]: s for s in _get("stops")}
        routes = _get("routes")
        places = _get("places")
        reviews = _get("reviews", {"order": "days_ago.asc"})
        transfers = _get("transfers")
    except (httpx.HTTPError, ValueError):
        STATUS.update(mode="memory", reason="read failed, using /data")
        data.reset()
        return {}
    if not places or not routes:
        return {}  # empty tables (not seeded yet): keep /data

    by_place = {}
    for r in reviews:
        by_place.setdefault(r["place_id"], []).append(
            {"author": r["author"], "rating": r["rating"], "days_ago": r.get("days_ago"), "lang": r["lang"], "text": r["body"]})
    data.override("places", {"source": "supabase", "places": [{
        "id": p["id"], "name": p["name"], "name_ta": p.get("name_ta"), "type": p["type"], "category": p.get("category"),
        "address": p.get("address"), "area": p.get("area"), "near_stop": p.get("near_stop"), "lat": p["lat"], "lng": p["lng"],
        "open": _hm(p.get("open_time")), "close": _hm(p.get("close_time")), "open_24h": p.get("open_24h", False),
        "women_run": p.get("women_run", False), "well_lit": p.get("well_lit", False),
        "can_wait_inside": p.get("can_wait_inside", False), "crowd_by_hour": p.get("crowd_by_hour") or {},
        "rating": p.get("rating"), "reviews_count": p.get("reviews_count", 0), "photo": p.get("photo"),
        "reviews": by_place.get(p["id"], []), "source": p.get("source", "live")} for p in places]})

    def stop_list(seq, extra=()):
        out = []
        for s in seq or []:
            st = stops.get(s["stop_id"], {})
            row = {"name": st.get("name", s["stop_id"]), "code": s["stop_id"], "min": s["min"], "lat": st.get("lat"),
                   "lng": st.get("lng"), "area": st.get("area")}
            row.update({k: s[k] for k in extra if s.get(k) is not None})
            out.append(row)
        return out

    buses = [{
        "id": r["id"], "number": r["number"], "mode": "bus", "name": r["name"], "is_free": r["free_for_women"],
        "free_for_women": r["free_for_women"], "fare_inr": r["fare_inr"], "fare_others_inr": r.get("fare_others_inr"),
        "operator": r.get("operator"), "stops": stop_list(r["stop_sequence"]), "first": _hm(r.get("first_departure")),
        "last": _hm(r.get("last_departure")), "frequency_minutes": r.get("frequency_min") or 15,
        "walk_start_min": r.get("walk_start_min") or 3, "walk_end_min": r.get("walk_end_min") or 2,
        "stops_well_lit": r.get("stops_well_lit"), "notes": r.get("notes"), "source": r.get("source", "live"),
    } for r in routes if r["mode"] == "bus"]
    metro_rules = next((r.get("fare_rules") for r in routes if r["mode"] == "metro" and r.get("fare_rules")), {}) or {}
    metro_lines = [{
        "id": r["id"], "name": r["name"], "color": r.get("color"), "first": _hm(r.get("first_departure")),
        "last": _hm(r.get("last_departure")), "headway_peak_min": r.get("headway_peak_min") or 6,
        "headway_offpeak_min": r.get("headway_offpeak_min") or 10, "peak_hours": r.get("peak_hours") or [],
        "women_coach": r.get("women_coach"), "stations": stop_list(r["stop_sequence"], ("platform", "best_exit")),
        "source": r.get("source", "live")} for r in routes if r["mode"] == "metro"]
    trains = [{
        "id": r["id"], "name": r["name"], "fare_inr": r["fare_inr"], "fare_first_class_inr": (r.get("fare_rules") or {}).get("first_class_inr"),
        "ladies_coaches": r.get("ladies_coaches") or [], "total_coaches": r.get("total_coaches") or 9,
        "ladies_special": r.get("ladies_special") or [], "first": _hm(r.get("first_departure")),
        "last_train": _hm(r.get("last_departure")), "frequency_minutes": r.get("frequency_min") or 15, "delays_sample": {},
        "stations": stop_list(r["stop_sequence"], ("platform",)), "source": r.get("source", "live")} for r in routes if r["mode"] == "train"]
    data.override("routes", {"source": "supabase", "routes": buses})
    if metro_lines:
        data.override("metro", {"source": "supabase", "fare_by_stations": metro_rules.get("by_stations", data.load("metro")["fare_by_stations"]),
                                "fare_max_inr": metro_rules.get("max_inr", 50), "lines": metro_lines})
    if trains:
        data.override("trains", {"source": "supabase", "lines": trains})
    data.override("transfers", {"source": "supabase", "transfers": [{
        "at": stops.get(t["at_stop"], {}).get("name", t["at_stop"]), "code": t["at_stop"], "from": t["from_mode"],
        "to": t["to_mode"], "walk_min": t["walk_min"], "lit": t["lit"], "note": t.get("note"), "source": t.get("source")} for t in transfers]})
    loaded = {"places": len(places), "reviews": len(reviews), "routes": len(routes), "stops": len(stops), "transfers": len(transfers)}
    STATUS["loaded"] = loaded
    return loaded


# ---------------------------------------------------------------- writes

def _write(method, table, rows=None, params=None):
    base, h = _rest()
    try:
        if method == "upsert":
            r = httpx.post(f"{base}/{table}", params={"on_conflict": "id"}, json=rows,
                           headers={**h, "Prefer": "resolution=merge-duplicates,return=minimal"}, timeout=TIMEOUT)
        elif method == "insert":
            r = httpx.post(f"{base}/{table}", json=rows, headers={**h, "Prefer": "return=minimal"}, timeout=TIMEOUT)
        else:
            r = httpx.delete(f"{base}/{table}", params=params, headers=h, timeout=TIMEOUT)
        ok = r.status_code < 300
    except httpx.HTTPError:
        ok = False
    with _lock:
        STATUS["writes_ok" if ok else "writes_failed"] += 1
    return ok


def persist(table: str, row: dict, method: str = "upsert", sync: bool = False):
    """Mirror one row to Supabase in the background (no-op in memory mode)."""
    if STATUS["mode"] != "supabase":
        return None
    if sync:
        return _write(method, table, [row])
    return _pool.submit(_write, method, table, [row])


def delete(table: str, row_id: str):
    if STATUS["mode"] == "supabase":
        _pool.submit(_write, "delete", table, None, {"id": f"eq.{row_id}"})


def status() -> dict:
    s = {k: v for k, v in STATUS.items() if k != "checked_at"}
    s["datasets"] = dict(data.SOURCE)
    return s
