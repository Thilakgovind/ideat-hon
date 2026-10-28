"""Seed Supabase with the deterministic sample data (safe to re-run).

    python -m backend.seed_supabase            # upsert everything, print counts per table
    python -m backend.seed_supabase --dry-run  # build rows only, print counts, no network

- Uses SUPABASE_URL + SUPABASE_SERVICE_KEY (backend only). Prints table names and counts only.
- Upserts by id; trip_events and request_log (no natural id) replace their source='sample' rows.
- Real MTC routes from data/gtfs_bus.json (ChennaiGTFS) go in as source='live', data_source='ChennaiGTFS (MTC)',
  with their stops. Needs migration 003_real_transit.sql (departures / one_way / free_note / data_source columns).
- DEMO_CONTACT_PHONE_1 / _2 (optional) replace the fake phones of Priya's first two contacts.
  Those real numbers go only to Supabase (private table), never to /data or the console.
"""
import json
import sys

import httpx

from backend import config, data
from backend.agents import route
from backend.seed.generate_sample import build

BATCH = 200
TIMEOUT = 30
ORDER = ["stops", "routes", "transfers", "places", "reviews", "users", "circle_contacts", "trips", "trip_events", "request_log"]
REPLACE_SAMPLE = {"trip_events", "request_log"}  # identity keys: delete sample rows, then insert


def _t(hhmm):
    return None if not hhmm else ("23:59:59" if hhmm == "23:59" else f"{hhmm}:00")


def rows_from(b: dict) -> dict:
    """Map the generated data onto the Supabase tables."""
    out = {"stops": [dict(s) for s in b["stops"]]}
    stop_ids = {s["id"] for s in out["stops"]}

    routes = []
    for r in b["routes_json"]["routes"]:
        routes.append({
            "id": r["id"], "number": r["number"], "mode": "bus", "name": r["name"], "operator": r.get("operator"),
            "free_for_women": r["free_for_women"], "fare_inr": r["fare_inr"], "fare_others_inr": r.get("fare_others_inr"),
            "stop_sequence": [{"stop_id": s["code"], "min": s["min"]} for s in r["stops"]],
            "first_departure": _t(r["first"]), "last_departure": _t(r["last"]), "frequency_min": r["frequency_minutes"],
            "stops_well_lit": r.get("stops_well_lit"), "walk_start_min": r.get("walk_start_min"),
            "walk_end_min": r.get("walk_end_min"), "notes": r.get("notes"), "source": "sample"})
    metro = b["metro_json"]
    for line in metro["lines"]:
        routes.append({
            "id": line["id"], "number": line["id"], "mode": "metro", "name": line["name"], "operator": "Metro (sample)",
            "fare_inr": metro["fare_by_stations"]["1"],
            "fare_rules": {"by_stations": metro["fare_by_stations"], "max_inr": metro["fare_max_inr"]},
            "stop_sequence": [{"stop_id": s["code"], "min": s["min"], "platform": s.get("platform"), "best_exit": s.get("best_exit")}
                              for s in line["stations"]],
            "first_departure": _t(line["first"]), "last_departure": _t(line["last"]),
            "headway_peak_min": line["headway_peak_min"], "headway_offpeak_min": line["headway_offpeak_min"],
            "peak_hours": line["peak_hours"], "women_coach": line["women_coach"], "color": line.get("color"), "source": "sample"})
    for line in b["trains_json"]["lines"]:
        routes.append({
            "id": line["id"], "number": line["id"], "mode": "train", "name": line["name"], "operator": "Suburban rail (sample)",
            "fare_inr": line["fare_inr"], "fare_rules": {"first_class_inr": line.get("fare_first_class_inr")},
            "stop_sequence": [{"stop_id": s["code"], "min": s["min"], "platform": s.get("platform")} for s in line["stations"]],
            "first_departure": _t(line["first"]), "last_departure": _t(line["last_train"]), "frequency_min": line["frequency_minutes"],
            "ladies_coaches": line["ladies_coaches"], "total_coaches": line["total_coaches"],
            "ladies_special": line.get("ladies_special"), "source": "sample"})
    routes.append({"id": "AUTO", "number": "AUTO", "mode": "auto", "name": "Auto-rickshaw estimate", "fare_inr": route.AUTO_BASE_INR,
                   "fare_rules": {"base_inr": route.AUTO_BASE_INR, "base_km": route.AUTO_BASE_KM, "per_km_inr": route.AUTO_PER_KM_INR,
                                  "night_multiplier": 1.5, "night_hours": "22:00-05:00", "road_factor": route.ROAD_FACTOR,
                                  "booking_links": route.BOOKING_LINKS},
                   "notes": "Estimate only. Book in an auto app.", "source": "sample"})
    # NOT NULL routes columns: sending null overrides the table default, so fill them here.
    route_defaults = {"free_for_women": False, "fare_inr": 0, "stop_sequence": [], "one_way": False, "source": "sample"}
    for r in routes:
        for k, v in route_defaults.items():
            if r.get(k) is None:
                r[k] = v
    gtfs_stops, gtfs_routes = gtfs_rows(stop_ids)
    out["stops"] += gtfs_stops
    routes += gtfs_routes
    out["routes"] = routes

    out["transfers"] = [{"id": f"tr{i + 1:02d}", "at_stop": t["code"], "from_mode": t["from"], "to_mode": t["to"],
                         "walk_min": t["walk_min"], "lit": t["lit"], "note": t.get("note"), "source": "sample"}
                        for i, t in enumerate(b["transfers_json"]["transfers"]) if t["code"] in stop_ids]

    places, reviews = [], []
    for p in b["places_json"]["places"]:
        places.append({
            "id": p["id"], "name": p["name"], "name_ta": p.get("name_ta"), "type": p["type"], "category": p.get("category"),
            "area": p["area"], "address": p.get("address"), "near_stop": p["near_stop"] if p["near_stop"] in stop_ids else None,
            "lat": p["lat"], "lng": p["lng"], "open_time": _t(p["open"]), "close_time": _t(p["close"]),
            "open_24h": p.get("open_24h", False), "women_run": p.get("women_run", False), "well_lit": p.get("well_lit", False),
            "can_wait_inside": p.get("can_wait_inside", False), "crowd_by_hour": p.get("crowd_by_hour", {}),
            "rating": p.get("rating"), "reviews_count": p.get("reviews_count", 0), "photo": p.get("photo"),
            "phone": None, "source": "sample"})
        for i, r in enumerate(p.get("reviews", [])):
            reviews.append({"id": f"r_{p['id']}_{i + 1}", "place_id": p["id"], "author": r["author"], "rating": r["rating"],
                            "lang": r.get("lang", "en"), "body": r["text"], "days_ago": r.get("days_ago"), "source": "sample"})
    out["places"], out["reviews"] = places, reviews

    users, contacts = [], []
    real = [config.env("DEMO_CONTACT_PHONE_1"), config.env("DEMO_CONTACT_PHONE_2")]
    for u in b["circle_json"]["users"]:
        users.append({"id": u["user_id"], "display_name": u["display_name"], "phone": None, "home_area": u.get("home_area"),
                      "start_area": u.get("start_area"), "lang": "en", "source": "sample"})
        for i, c in enumerate(u["contacts"]):
            phone = c.get("phone")
            if u["user_id"] == "u_demo" and i < 2 and real[i]:
                phone = real[i]  # your verified test number, from .env only
            contacts.append({"id": c["id"], "user_id": u["user_id"], "label": c["label"], "label_ta": c.get("label_ta"),
                             "relation": c.get("relation"), "phone": phone, "accepted": c.get("accepted", False),
                             "status": c.get("status"), "area": c.get("area"), "lat": c.get("lat"), "lng": c.get("lng"),
                             "source": "sample"})
    out["users"], out["circle_contacts"] = users, contacts
    out["trips"] = [dict(t) for t in b["trips"]]
    out["trip_events"] = [dict(e) for e in b["trip_events"]]
    out["request_log"] = [dict(r) for r in b["request_log"]]
    return out


def _nearest_area(lat, lng):
    return min(data.areas(), key=lambda a: data.haversine_m(lat, lng, a["lat"], a["lng"]))["name"]


def gtfs_rows(existing_stop_ids=()) -> tuple:
    """Real MTC routes + their stops from data/gtfs_bus.json (empty if the file is missing)."""
    path = config.DATA_DIR / "gtfs_bus.json"
    if not path.exists():
        return [], []
    feed = json.loads(path.read_text(encoding="utf-8"))
    stops, routes = {}, []
    for r in feed["routes"]:
        for s in r["stops"]:
            if s["code"] not in stops and s["code"] not in existing_stop_ids:
                stops[s["code"]] = {"id": s["code"], "name": s["name"], "area": s.get("area") or _nearest_area(s["lat"], s["lng"]),
                                    "kind": "bus_stop", "lat": s["lat"], "lng": s["lng"], "source": "live",
                                    "data_source": r["source"]}
        routes.append({
            "id": r["id"], "number": r["number"], "mode": "bus", "name": r["name"], "operator": r.get("operator"),
            "free_for_women": r["free_for_women"], "fare_inr": r["fare_inr"], "fare_others_inr": r.get("fare_others_inr"),
            # area is per route: the stop that stands for an app area on THIS route
            "stop_sequence": [{"stop_id": s["code"], "min": s["min"], "area": s.get("area")} for s in r["stops"]],
            "first_departure": _t(r["first"]), "last_departure": _t(r["last"]), "frequency_min": max(1, r["frequency_minutes"]),
            "walk_start_min": r.get("walk_start_min"), "walk_end_min": r.get("walk_end_min"), "notes": r.get("notes"),
            "departures": r["departures"], "one_way": True, "free_note": r.get("free_note"),
            "source": "live", "data_source": r["source"], "source_url": r.get("source_url")})
    return list(stops.values()), routes


def uniform(rows: list) -> list:
    """PostgREST bulk insert needs every row to have the same keys (PGRST102).
    Give each row the full column set of the table; missing values become null."""
    columns = list(dict.fromkeys(k for r in rows for k in r))
    return [{k: r.get(k) for k in columns} for r in rows]


class Rest:
    def __init__(self):
        url = config.env("SUPABASE_URL").rstrip("/")
        key = config.env("SUPABASE_SERVICE_KEY")
        self.base = f"{url}/rest/v1"
        self.client = httpx.Client(timeout=TIMEOUT, headers={"apikey": key, "Authorization": f"Bearer {key}"})

    @staticmethod
    def _check(r, table, what):
        if r.status_code >= 300:
            try:
                code = r.json().get("code", "")
            except ValueError:
                code = ""
            raise RuntimeError(f"{table}: {what} failed (HTTP {r.status_code} {code})")  # no row data, no keys

    def upsert(self, table, rows):
        rows = uniform(rows)
        for i in range(0, len(rows), BATCH):
            r = self.client.post(f"{self.base}/{table}", params={"on_conflict": "id"}, json=rows[i:i + BATCH],
                                 headers={"Prefer": "resolution=merge-duplicates,return=minimal"})
            self._check(r, table, "upsert")

    def replace_sample(self, table, rows):
        self._check(self.client.delete(f"{self.base}/{table}", params={"source": "eq.sample"}), table, "delete sample rows")
        rows = uniform(rows)
        for i in range(0, len(rows), BATCH):
            self._check(self.client.post(f"{self.base}/{table}", json=rows[i:i + BATCH], headers={"Prefer": "return=minimal"}),
                        table, "insert")

    def count(self, table):
        r = self.client.get(f"{self.base}/{table}", params={"select": "id", "limit": 1},
                            headers={"Prefer": "count=exact", "Range": "0-0"})
        self._check(r, table, "count")
        return int(r.headers.get("content-range", "*/0").split("/")[-1])


def seed(rest=None) -> dict:
    rows = rows_from(build())
    rest = rest or Rest()
    for table in ORDER:
        (rest.replace_sample if table in REPLACE_SAMPLE else rest.upsert)(table, rows[table])
    return {table: rest.count(table) for table in ORDER}


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if "--dry-run" in argv:
        counts = {t: len(v) for t, v in rows_from(build()).items()}
        label = "rows built (dry run, nothing sent)"
    else:
        if not (config.env("SUPABASE_URL") and config.env("SUPABASE_SERVICE_KEY")):
            print("SUPABASE_URL / SUPABASE_SERVICE_KEY: MISSING - nothing seeded (the app keeps using /data JSON)")
            return 1
        try:
            counts = seed()
        except (RuntimeError, httpx.HTTPError) as e:
            print(f"seed FAILED: {e if isinstance(e, RuntimeError) else type(e).__name__}")
            return 1
        label = "rows in Supabase after seeding"
    print(label)
    for t in ORDER:
        print(f"  {t:<16} {counts[t]}")
    print(f"  {'TOTAL':<16} {sum(counts[t] for t in ORDER)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
