"""Real MTC bus routes from ChennaiGTFS -> data/gtfs_bus.json.

    git clone --depth 1 https://github.com/ungalsoththu/ChennaiGTFS.git <dir>
    python -m backend.seed.import_gtfs <dir>/data/mtc

- Imports every MTC route that runs between a pair of app areas (default: the demo
  pair Anna Nagar West <-> Nungambakkam, both directions). One row per route_id
  (= one direction), using its most common stop pattern on the daily ("Regular") service.
- Keeps the real per-trip departure times, so the app never invents a frequency.
- Free for women: Vidiyal Payanam makes ordinary (white-board) MTC buses free. GTFS does
  not say which trips use ordinary buses, so every row carries free_note saying so.
- Data: ChennaiGTFS (UngalSoththu), ODbL / PDDL. Timetables from the MTC app, collected 2026-04.
"""
import csv
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

from .. import data

OUT = Path(__file__).resolve().parents[2] / "data" / "gtfs_bus.json"
DEFAULT_PAIRS = [("Anna Nagar West", "Nungambakkam")]
NAME_MATCH_MAX_M = 2500   # a stop named after an area must still be near it (feed has a few misplaced stops)
NEAR_AREA_M = 600         # otherwise the nearest stop this close to the area centre stands for the area
SOURCE = "ChennaiGTFS (MTC)"
SOURCE_URL = "https://github.com/ungalsoththu/ChennaiGTFS"
FREE_NOTE = "Free on ordinary (white-board) MTC buses under Vidiyal Payanam. Deluxe / AC buses are paid."


def _read(d: Path, name: str):
    with open(d / name, encoding="utf-8") as f:
        yield from csv.DictReader(f)


def _minutes(hms: str) -> int:
    h, m, *_ = hms.split(":")
    return int(h) * 60 + int(m)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s.lower())).strip()


def tag_areas(stops: list, areas: list) -> None:
    """Sets stop["area"] for the one stop on this route that stands for each app area.
    First pass: stops named after the area. Second pass: nearest stop for areas still unmatched."""
    def free(cands, a):
        cands = [s for s in cands if not s.get("area")]
        return min(cands, key=lambda s: data.haversine_m(a["lat"], a["lng"], s["lat"], s["lng"])) if cands else None

    unmatched = []
    for a in areas:
        key = _norm(a["name"])
        named = [s for s in stops if re.search(rf"(?<!\w){re.escape(key)}(?!\w)", _norm(s["name"]))
                 and data.haversine_m(a["lat"], a["lng"], s["lat"], s["lng"]) <= NAME_MATCH_MAX_M]
        pick = free(named, a)
        if pick:
            pick["area"] = a["name"]
        else:
            unmatched.append(a)
    for a in unmatched:
        near = [s for s in stops if data.haversine_m(a["lat"], a["lng"], s["lat"], s["lng"]) <= NEAR_AREA_M]
        pick = free(near, a)
        if pick:
            pick["area"] = a["name"]


def build(mtc_dir: Path, pairs=DEFAULT_PAIRS) -> dict:
    areas = data.areas()
    stops = {r["stop_id"]: r for r in _read(mtc_dir, "stops.txt")}
    routes = {r["route_id"]: r for r in _read(mtc_dir, "routes.txt")}
    trips = {r["trip_id"]: r for r in _read(mtc_dir, "trips.txt") if r["service_id"] == "Regular"}
    times = defaultdict(list)
    for r in _read(mtc_dir, "stop_times.txt"):
        if r["trip_id"] in trips:
            times[r["trip_id"]].append((int(r["stop_sequence"]), r["stop_id"], _minutes(r["departure_time"])))

    patterns = defaultdict(list)  # (route_id, stop ids) -> [trip stop times]
    for tid, st in times.items():
        st.sort()
        patterns[(trips[tid]["route_id"], tuple(s[1] for s in st))].append(st)
    best = {}
    for (rid, pat), ts in patterns.items():
        if rid not in best or len(ts) > len(best[rid][1]):
            best[rid] = (pat, ts)

    rows = []
    for rid, (pat, ts) in best.items():
        stop_rows = []
        for i, sid in enumerate(pat):
            s = stops[sid]
            offset = round(statistics.median(t[i][2] - t[0][2] for t in ts))
            stop_rows.append({"name": s["stop_name"].strip(), "code": f"MTC{sid}", "min": offset,
                              "lat": round(float(s["stop_lat"]), 5), "lng": round(float(s["stop_lon"]), 5)})
        tag_areas(stop_rows, areas)
        tagged = {s["area"] for s in stop_rows if s.get("area")}
        if not any(a in tagged and b in tagged for a, b in pairs):
            continue
        deps = sorted({t[0][2] % (24 * 60) for t in ts})
        gaps = [b - a for a, b in zip(deps, deps[1:])]
        r = routes[rid]
        number = re.sub(r"\s+", " ", r["route_short_name"]).strip()
        rows.append({
            "id": f"MTC-{rid}", "number": number, "mode": "bus",
            "name": re.sub(r"\s+", " ", r["route_long_name"]).strip().replace(" TO ", " to "),
            "operator": "MTC", "is_free": True, "free_for_women": True, "free_note": FREE_NOTE,
            "fare_inr": 0, "fare_others_inr": None,
            "stops": stop_rows, "one_way": True,
            "departures": [data.fmt_minutes(d) for d in deps],
            "first": data.fmt_minutes(deps[0]), "last": data.fmt_minutes(deps[-1]),
            "frequency_minutes": round(statistics.median(gaps)) if gaps else 60,
            "walk_start_min": 3, "walk_end_min": 2,
            "notes": f"Real MTC timetable: {len(deps)} buses a day from {stop_rows[0]['name']}.",
            "source": SOURCE, "source_url": SOURCE_URL,
        })
    rows.sort(key=lambda r: (-len(r["departures"]), r["number"], r["id"]))
    return {
        "source": SOURCE, "source_url": SOURCE_URL, "license": "ODbL / PDDL (ChennaiGTFS by UngalSoththu)",
        "collected": "MTC app timetable, 2026-04 (ChennaiGTFS v0.2.0)",
        "note": FREE_NOTE + " Timetables are scheduled times, not live tracking.",
        "pairs": [list(p) for p in pairs], "routes": rows,
    }


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__)
        return 2
    out = build(Path(argv[0]))
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    counts = Counter(r["number"] for r in out["routes"])
    print(f"wrote {OUT.name}: {len(out['routes'])} route directions ({', '.join(f'{k} x{v}' for k, v in counts.items())})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
