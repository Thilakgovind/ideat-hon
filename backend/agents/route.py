"""Route agent: bus / metro / train / auto options from the /data files only.

Builds on the matching idea in agents/route_and_sakhi_lookup.py, but matches
whole words first so "T Nagar" never matches "Thirumangalam".
"""
import re
from difflib import SequenceMatcher

from .. import data
from ..guardrails import verify_options

AUTO_BASE_INR = 50
AUTO_BASE_KM = 1.8
AUTO_PER_KM_INR = 25
AUTO_SPEED_KMPH = 22
ROAD_FACTOR = 1.35
BOOKING_LINKS = {
    "Namma Yatri": "https://nammayatri.in/",
    "Rapido": "https://www.rapido.bike/",
    "Ola": "https://www.olacabs.com/",
    "Uber": "https://www.uber.com/in/en/",
}


# ---------- place matching ----------

def norm(s: str) -> str:
    s = (s or "").lower().replace(".", " ")
    return re.sub(r"\s+", " ", s).strip()


def _all_stop_names():
    names = []
    for r in data.routes():
        names += [s["name"] for s in r["stops"]]
    for line in data.metro()["lines"]:
        names += [s["name"] for s in line["stations"]]
    for line in data.trains():
        names += [s["name"] for s in line["stations"]]
    return names


def _keys():
    """normalized key -> canonical place name."""
    keys = {}
    for a in data.areas():
        keys[norm(a["name"])] = a["name"]
        keys[a["name_ta"]] = a["name"]
        for alias in a.get("aliases", []):
            keys.setdefault(norm(alias), a["name"])
    for stop in _all_stop_names():
        keys.setdefault(norm(stop), stop)
    return keys


def match_place(query: str):
    """Best canonical place for free text, or None. Never guesses below threshold."""
    q = norm(query)
    if not q:
        return None
    keys = _keys()
    if q in keys:
        return keys[q]
    # whole-word containment, longest key wins ("nungambakkam bus", "to anna nagar west")
    contained = [k for k in keys if re.search(rf"(?<!\w){re.escape(k)}(?!\w)", q)]
    if contained:
        return keys[max(contained, key=len)]
    best, score = None, 0.0
    for k, name in keys.items():
        s = SequenceMatcher(None, q, k).ratio()
        if len(q) >= 4 and any(w.startswith(q) for w in k.split()):
            s = max(s, 0.8)
        if s > score:
            best, score = name, s
    return best if score >= 0.75 else None


def find_places_in_text(text: str) -> list:
    """All known places mentioned in text, in order of appearance."""
    t = norm(text)
    found = []
    for k, name in _keys().items():
        for m in re.finditer(rf"(?<!\w){re.escape(k)}(?!\w)", t):
            found.append((m.start(), m.end(), name))
    # drop matches contained inside a longer match ("anna nagar" inside "anna nagar west")
    found.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    result, last_end = [], -1
    for start, end, name in found:
        if start >= last_end:
            result.append(name)
            last_end = end
    return result


def _belongs(stop_name: str, place: str) -> bool:
    if norm(stop_name) == norm(place):
        return True
    for a in data.areas():
        if a["name"] == place:
            return norm(stop_name) in {norm(x) for x in a.get("aliases", [])}
    return False


def _index(stops, place):
    for i, s in enumerate(stops):
        if _belongs(s["name"], place):
            return i
    return None


# ---------- departures ----------

def _bus_times(route, offset, after, count=3):
    first, last, freq = data.to_minutes(route["first"]), data.to_minutes(route["last"]), route["frequency_minutes"]
    out, d = [], first
    while d <= last and len(out) < count:
        if d + offset >= after:
            out.append(d + offset)
        d += freq
    return out


def _metro_headway(line, minutes):
    for span in line["peak_hours"]:
        a, b = span.split("-")
        if data.to_minutes(a) <= minutes <= data.to_minutes(b):
            return line["headway_peak_min"]
    return line["headway_offpeak_min"]


def _metro_times(line, offset, after, count=3):
    first, last = data.to_minutes(line["first"]), data.to_minutes(line["last"])
    out, d = [], first
    while d <= last and len(out) < count:
        if d + offset >= after:
            out.append(d + offset)
        d += _metro_headway(line, d)
    return out


def _train_times(line, offset, after, count=3):
    first, last, freq = data.to_minutes(line["first"]), data.to_minutes(line["last_train"]), line["frequency_minutes"]
    out, d = [], first
    while d <= last and len(out) < count:
        if d + offset >= after:
            delay = line.get("delays_sample", {}).get(data.fmt_minutes(d), 0)
            out.append({"time": data.fmt_minutes(d + offset), "delay_min": delay,
                        "ladies_special": data.fmt_minutes(d) in line.get("ladies_special", [])})
        d += freq
    return out


def _metro_fare(n_stations):
    table = data.metro()["fare_by_stations"]
    return table.get(str(n_stations), data.metro()["fare_max_inr"])


# ---------- legs ----------

def _walk(minutes, label="Walk"):
    return {"mode": "walk", "label": label, "minutes": minutes}


def _bus_leg(route, i, j, at):
    stops = route["stops"]
    times = _bus_times(route, stops[i]["min"], at)
    return {
        "mode": "bus", "route_id": route["id"], "label": route["number"],
        "from": stops[i]["name"], "from_code": stops[i]["code"],
        "to": stops[j]["name"], "to_code": stops[j]["code"],
        "minutes": stops[j]["min"] - stops[i]["min"],
        "is_free": route["free_for_women"], "fare_inr": 0 if route["free_for_women"] else route["fare_inr"],
        "next": [data.fmt_minutes(t) for t in times], "_next_min": times,
        "stops_well_lit": route.get("stops_well_lit", False),
        "stops": [s["name"] for s in stops[i:j + 1]],
        "source": route.get("source", "sample"),
    }


def _metro_leg(line, i, j, at):
    st = line["stations"]
    times = _metro_times(line, st[i]["min"], at)
    return {
        "mode": "metro", "route_id": line["id"], "label": "Metro", "line": line["name"], "color": line["color"],
        "from": st[i]["name"], "from_code": st[i]["code"], "to": st[j]["name"], "to_code": st[j]["code"],
        "minutes": st[j]["min"] - st[i]["min"], "is_free": False, "fare_inr": _metro_fare(j - i),
        "platform": st[i]["platform"], "women_coach": line["women_coach"], "best_exit": st[j]["best_exit"],
        "next": [data.fmt_minutes(t) for t in times], "_next_min": times,
        "stations": [{"name": s["name"], "min_from_board": s["min"] - st[i]["min"]} for s in st[i:j + 1]],
        "source": line.get("source", "sample"),
    }


def _train_leg(line, i, j, at):
    st = line["stations"]
    times = _train_times(line, st[i]["min"], at)
    return {
        "mode": "train", "route_id": line["id"], "label": "Train", "line": line["name"],
        "from": st[i]["name"], "from_code": st[i]["code"], "to": st[j]["name"], "to_code": st[j]["code"],
        "minutes": st[j]["min"] - st[i]["min"], "is_free": False, "fare_inr": line["fare_inr"],
        "platform": st[i]["platform"], "ladies_coaches": line["ladies_coaches"],
        "total_coaches": line["total_coaches"], "last_train": line["last_train"],
        "next": [t["time"] for t in times], "next_detail": times,
        "_next_min": [data.to_minutes(t["time"]) + t["delay_min"] for t in times],
        "source": line.get("source", "sample"),
    }


def _option(kind, legs, at, extra=None):
    transit = [l for l in legs if l["mode"] in ("bus", "metro", "train")]
    total = sum(l["minutes"] for l in legs)
    # reach time: wait for the first transit departure, then ride the rest
    reach = at + total
    if transit and transit[0].get("_next_min"):
        walk_before = sum(l["minutes"] for l in legs[: legs.index(transit[0])])
        wait = max(0, transit[0]["_next_min"][0] - (at + walk_before))
        reach = at + total + wait
    opt = {
        "id": ":".join([kind] + [l["route_id"] for l in transit] + [transit[0]["from_code"] if transit else ""]),
        "kind": kind,
        "legs": [{k: v for k, v in l.items() if not k.startswith("_")} for l in legs],
        "total_min": total,
        "reach_by": data.fmt_minutes(reach),
        "fare_inr": sum(l.get("fare_inr", 0) for l in legs),
        "is_free": all(l.get("is_free") for l in transit) if transit else False,
        "switches": max(0, len(transit) - 1),
        "board_at": transit[0]["from"] if transit else None,
        "board_code": transit[0].get("from_code") if transit else None,
        "alight_code": transit[-1].get("to_code") if transit else None,
        "next": transit[0]["next"] if transit else [],
        "source": "sample",
    }
    opt.update(extra or {})
    return opt


def _auto_option(frm, to, at):
    a, b = data.area_coords(frm), data.area_coords(to)
    if not a or not b:
        return None
    km = data.haversine_m(*a, *b) / 1000 * ROAD_FACTOR
    minutes = round(km / AUTO_SPEED_KMPH * 60) + 3
    fare = AUTO_BASE_INR + max(0.0, km - AUTO_BASE_KM) * AUTO_PER_KM_INR
    night = at >= 22 * 60 or at < 5 * 60
    if night:
        fare *= 1.5
    fare = int(round(fare / 10.0) * 10)
    return {
        "id": "auto", "kind": "auto",
        "legs": [{"mode": "auto", "label": "Auto", "from": frm, "to": to, "minutes": minutes, "fare_inr": fare, "is_free": False}],
        "total_min": minutes, "reach_by": data.fmt_minutes(at + minutes), "fare_inr": fare,
        "fare_is_estimate": True, "night_fare": night, "distance_km": round(km, 1),
        "is_free": False, "switches": 0, "board_at": None, "board_code": None, "alight_code": None, "next": [],
        "booking_links": BOOKING_LINKS, "source": "sample",
    }


# ---------- public API ----------

def plan(frm: str, to: str, time=None, with_child: bool = False, modes=None) -> dict:
    """All ways from `frm` to `to` at `time`. Only data-backed options."""
    at = data.parse_time(time)
    f, t = match_place(frm), match_place(to)
    if not f or not t:
        return {"error": "no_match", "unmatched": [x for x, m in ((frm, f), (to, t)) if not m],
                "from": f, "to": t, "options": []}
    if f == t:
        return {"error": "same_place", "from": f, "to": t, "options": []}

    options, not_running = [], []
    for r in data.routes():
        i, j = _index(r["stops"], f), _index(r["stops"], t)
        if i is not None and j is not None and i < j:
            leg = _bus_leg(r, i, j, at + r["walk_start_min"])
            if not leg["_next_min"]:
                not_running.append(r["number"])
                continue
            options.append(_option("bus", [_walk(r["walk_start_min"]), leg, _walk(r["walk_end_min"])], at))

    for tr in data.transfers():
        for r in data.routes():
            i, k = _index(r["stops"], f), _index(r["stops"], tr["at"])
            if i is None or k is None or i >= k:
                continue
            for line in data.metro()["lines"]:
                m, n = _index(line["stations"], tr["at"]), _index(line["stations"], t)
                if m is None or n is None or m >= n:
                    continue
                bus = _bus_leg(r, i, k, at + r["walk_start_min"])
                if not bus["_next_min"]:
                    continue
                metro_ready = bus["_next_min"][0] + bus["minutes"] + tr["walk_min"]
                met = _metro_leg(line, m, n, metro_ready)
                if not met["_next_min"]:
                    continue
                legs = [_walk(r["walk_start_min"]), bus, _walk(tr["walk_min"], f"Walk to Metro ({tr['at']})"), met, _walk(2)]
                options.append(_option("bus+metro", legs, at, {"switch_info": {
                    "at": tr["at"], "walk_min": tr["walk_min"], "lit": tr["lit"], "note": tr["note"]}}))

    for line in data.metro()["lines"]:
        i, j = _index(line["stations"], f), _index(line["stations"], t)
        if i is not None and j is not None and i < j:
            met = _metro_leg(line, i, j, at + 3)
            if met["_next_min"]:
                options.append(_option("metro", [_walk(3), met, _walk(2)], at))

    for line in data.trains():
        i, j = _index(line["stations"], f), _index(line["stations"], t)
        if i is not None and j is not None and i < j:
            tl = _train_leg(line, i, j, at + 5)
            if tl["_next_min"]:
                options.append(_option("train", [_walk(5), tl, _walk(3)], at))

    auto = _auto_option(f, t, at)
    if auto:
        options.append(auto)

    if modes:
        options = [o for o in options if any(m in o["kind"] for m in modes)]
    options = verify_options(options)
    return {
        "from": f, "to": t, "from_ta": data.area_ta(f), "to_ta": data.area_ta(t),
        "time": data.fmt_minutes(at), "with_child": with_child,
        "options": options, "not_running_now": not_running, "source": "sample",
    }


def arrivals(stop: str, time=None, free_only: bool = False) -> dict:
    """Next buses at a stop (Free bus tracker screen)."""
    at = data.parse_time(time)
    place = match_place(stop)
    if not place:
        return {"error": "no_match", "stop": stop, "arrivals": []}
    out = []
    for r in data.routes():
        i = _index(r["stops"], place)
        if i is None or i == len(r["stops"]) - 1:
            continue
        if free_only and not r["free_for_women"]:
            continue
        for t in _bus_times(r, r["stops"][i]["min"], at):
            out.append({"route_id": r["id"], "number": r["number"], "towards": r["stops"][-1]["name"],
                        "time": data.fmt_minutes(t), "in_min": t - at, "is_free": r["free_for_women"],
                        "fare_inr": 0 if r["free_for_women"] else r["fare_inr"]})
    out.sort(key=lambda x: x["in_min"])
    return {"stop": place, "time": data.fmt_minutes(at), "arrivals": out, "source": "sample"}


def find_option(frm, to, time, option_id):
    """Re-plan on the server and return the option with this id (never trust client fares)."""
    result = plan(frm, to, time)
    for o in result.get("options", []):
        if o["id"] == option_id:
            return o, result
    return None, result
