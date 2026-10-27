"""Deterministic Chennai sample data for SafePath (fixed seed, safe to re-run).

    python -m backend.seed.generate_sample          # rewrite /data JSON + print counts

- Keeps the hand-made demo rows in /data (21G, Lakshmi kiosk, walk paths, Priya's circle)
  and adds generated rows marked "generated": true. Re-running replaces only those.
- Every row is "source": "sample". Business names are generic / fictional.
- Places never carry phone numbers. Circle phones are FAKE (+91 00000 0xxxx).
  Real test numbers come only from DEMO_CONTACT_PHONE_1/2 at seed time (never written here).
- Generated routes never join the Anna Nagar West <-> Nungambakkam demo pair,
  so the demo route and its tests stay exactly as designed.
"""
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
SEED = 2026

AREAS = {  # name: (lat, lng, Tamil)
    "Anna Nagar": (13.0850, 80.2101, "அண்ணா நகர்"),
    "Nungambakkam": (13.0604, 80.2422, "நுங்கம்பாக்கம்"),
    "Koyambedu": (13.0694, 80.1948, "கோயம்பேடு"),
    "T Nagar": (13.0418, 80.2341, "தி. நகர்"),
    "Egmore": (13.0784, 80.2610, "எழும்பூர்"),
    "Mylapore": (13.0339, 80.2619, "மயிலாப்பூர்"),
    "Adyar": (13.0012, 80.2565, "அடையாறு"),
    "Velachery": (12.9815, 80.2180, "வேளச்சேரி"),
    "Guindy": (13.0067, 80.2206, "கிண்டி"),
    "Tambaram": (12.9249, 80.1000, "தாம்பரம்"),
    "Vadapalani": (13.0500, 80.2121, "வடபழனி"),
    "Kilpauk": (13.0829, 80.2417, "கீழ்ப்பாக்கம்"),
}
NEW_AREA_ROWS = [  # areas.json entries that the app does not have yet
    {"name": "Mylapore", "name_ta": "மயிலாப்பூர்", "aliases": ["mylapur"], "lat": 13.0339, "lng": 80.2619},
    {"name": "Adyar", "name_ta": "அடையாறு", "aliases": ["adayar"], "lat": 13.0012, "lng": 80.2565},
]

# ~40 extra bus stops (names are neighbourhood / landmark style, all sample).
# Demo stops ANW / NMB / Anna Nagar names are deliberately NOT reused here.
NEW_STOPS = {
    "Anna Nagar": ["Shanthi Colony", "Anna Nagar Roundtana", "Blue Star"],
    "Nungambakkam": ["Valluvar Kottam", "Sterling Road", "Loyola College"],
    "Koyambedu": ["Koyambedu Market", "CMBT Bus Terminus", "Arumbakkam"],
    "T Nagar": ["Pondy Bazaar", "Panagal Park", "T Nagar Bus Terminus", "Mambalam Station"],
    "Egmore": ["Egmore Station", "Pantheon Road", "Ega Theatre"],
    "Mylapore": ["Mylapore", "Mandaveli", "Luz Corner", "Santhome"],
    "Adyar": ["Adyar", "Adyar Depot", "Kasturba Nagar", "Thiruvanmiyur"],
    "Velachery": ["Velachery Bus Terminus", "Vijaya Nagar", "Taramani"],
    "Guindy": ["Guindy Industrial Estate", "Kathipara", "Saidapet"],
    "Tambaram": ["Tambaram", "Tambaram Sanatorium", "Chromepet", "Pallavaram"],
    "Vadapalani": ["Vadapalani Bus Depot", "Ashok Nagar", "KK Nagar"],
    "Kilpauk": ["Kilpauk Garden", "Purasawalkam", "Chetpet Lake"],
}

# Bus routes as (number, area path). Stops are picked per area in order.
NEW_ROUTES = [
    ("5D", ["T Nagar", "Vadapalani", "Koyambedu"]), ("27C", ["Egmore", "Kilpauk", "Koyambedu"]),
    ("23C", ["Egmore", "Mylapore", "Adyar"]), ("29C", ["T Nagar", "Mylapore", "Adyar"]),
    ("47A", ["Guindy", "Velachery", "Adyar"]), ("12B", ["Kilpauk", "Egmore", "Mylapore"]),
    ("18A", ["Tambaram", "Guindy", "T Nagar"]), ("21L", ["Guindy", "T Nagar", "Egmore"]),
    ("45B", ["Velachery", "Guindy", "Vadapalani"]), ("51P", ["Tambaram", "Velachery", "Adyar"]),
    ("54", ["Koyambedu", "Vadapalani", "Guindy"]), ("99", ["Adyar", "Mylapore", "Egmore"]),
    ("119", ["Velachery", "Guindy", "T Nagar"]), ("570", ["Koyambedu", "Guindy", "Tambaram"]),
    ("M70", ["Koyambedu", "Vadapalani", "T Nagar"]), ("147", ["Anna Nagar", "Kilpauk", "Egmore"]),
    ("7M", ["Mylapore", "T Nagar", "Vadapalani"]), ("41D", ["Kilpauk", "Koyambedu", "Vadapalani"]),
    ("A1", ["Tambaram", "Guindy", "Adyar"]),  # AC deluxe (paid)
]
PAID_ROUTES = {"A1", "570", "M70"}

BLUE_LINE = [  # sample Blue Line (illustrative order / minutes)
    ("Chennai Central Metro", "Egmore", 0), ("Government Estate", "Egmore", 3), ("LIC", "Nungambakkam", 5),
    ("Thousand Lights", "Nungambakkam", 7), ("AG-DMS", "T Nagar", 9), ("Nandanam", "T Nagar", 11),
    ("Saidapet Metro", "Guindy", 13), ("Little Mount", "Guindy", 15), ("Guindy Metro", "Guindy", 17),
    ("Alandur", "Guindy", 19), ("Meenambakkam", "Tambaram", 23), ("Airport", "Tambaram", 26),
]
MRTS_LINE = [  # sample MRTS (Beach - Velachery)
    ("Park Town", "Egmore", 0), ("Chintadripet", "Egmore", 4), ("Light House", "Mylapore", 9),
    ("Thirumayilai", "Mylapore", 12), ("Mandaveli MRTS", "Mylapore", 14), ("Kotturpuram", "Adyar", 17),
    ("Kasturba Nagar MRTS", "Adyar", 20), ("Indira Nagar", "Adyar", 22), ("Thiruvanmiyur MRTS", "Adyar", 24),
    ("Taramani MRTS", "Velachery", 27), ("Perungudi", "Velachery", 30), ("Velachery MRTS", "Velachery", 33),
]

TRANSFER_SPOTS = [  # (at stop name, from, to, walk_min, lit, note)
    ("Guindy Industrial Estate", "bus", "metro", 6, True, "Covered skywalk to Guindy Metro"),
    ("Saidapet", "bus", "metro", 5, True, "Main road crossing with signal"),
    ("Saidapet", "bus", "train", 4, True, "Steps to the suburban platform"),
    ("Pondy Bazaar", "bus", "metro", 7, True, "Busy shopping street to AG-DMS"),
    ("Egmore Station", "train", "metro", 5, True, "Inside the station complex"),
    ("Egmore Station", "bus", "train", 3, True, "Bus bay at the station entrance"),
    ("Tambaram", "bus", "train", 3, True, "Bus stand next to the station"),
    ("Chromepet", "bus", "train", 5, False, "Subway can be dark late at night"),
    ("Pallavaram", "bus", "train", 6, False, "Quiet lane after 10 pm"),
    ("Velachery Bus Terminus", "bus", "train", 6, True, "Road to MRTS station is well lit"),
    ("Mylapore", "bus", "train", 8, False, "Back street to Thirumayilai MRTS"),
    ("Thiruvanmiyur", "bus", "train", 5, True, "Main road to MRTS"),
    ("Mambalam Station", "bus", "train", 4, True, "Crowded foot overbridge"),
    ("Vadapalani Bus Depot", "bus", "bus", 2, True, "Same depot, change bays"),
    ("Kathipara", "bus", "bus", 4, False, "Wide junction, use the pedestrian subway"),
    ("CMBT Bus Terminus", "bus", "bus", 5, True, "Inside the terminus"),
    ("Taramani", "bus", "train", 7, False, "Long walk past the IT park"),
    ("Park Town", "train", "train", 6, True, "Foot overbridge to Central suburban"),
]

PLACE_TYPES = ["pharmacy", "grocery", "tea_shop", "atm", "hospital", "police_booth", "shg_kiosk", "petrol_bunk", "bus_shelter"]
TYPE_WEIGHTS = [4, 4, 4, 2, 1, 1, 2, 1, 1]
NAME_PARTS = {
    "pharmacy": (["Sri Lakshmi", "Annai", "Sakthi", "Jaya", "Sri Murugan", "Kaveri", "Sree Devi", "Arul"], ["Medicals", "Pharmacy", "Medical Stores"]),
    "grocery": (["Annai", "Selvi", "Meena", "Kumaran", "Sri Balaji", "Thangam", "Velu", "Amudha"], ["Stores", "Provision Store", "Mini Mart"]),
    "tea_shop": (["Amma", "Ganesh", "Raja", "Kalai", "Murugan", "Pandian", "Bharathi", "Sundar"], ["Tea Stall", "Tea Kadai", "Tiffin & Tea"]),
    "atm": (["Bank ATM"], [""]),
    "hospital": (["City", "Area", "Community", "Women & Child"], ["Clinic (24 h)", "Hospital (24 h)", "Health Centre"]),
    "police_booth": (["Police Booth"], [""]),
    "shg_kiosk": (["Sakhi", "Mahalir", "Thozhi", "Annai", "Pengal", "Kalpana"], ["SHG Kiosk", "SHG Snacks", "Women's Coop Kiosk"]),
    "petrol_bunk": (["Petrol Bunk"], [""]),
    "bus_shelter": (["Bus Shelter"], [""]),
}
STREETS = ["Main Road", "High Road", "2nd Avenue", "Market Street", "Station Road", "Temple Street", "Bazaar Road", "Gandhi Street"]
CATEGORY = {"pharmacy": "Pharmacy", "grocery": "Groceries", "tea_shop": "Tea & snacks", "atm": "ATM",
            "hospital": "Clinic / hospital", "police_booth": "Police & help", "shg_kiosk": "SHG kiosk",
            "petrol_bunk": "Petrol bunk", "bus_shelter": "Bus & metro"}

FIRST_NAMES = ["Deepa", "Farhana", "Meena", "Kavitha", "Revathi", "Shalini", "Nisha", "Anitha", "Divya", "Saranya",
               "Priyanka", "Gayathri", "Lakshmi", "Fathima", "Sangeetha", "Malathi", "Jothi", "Ramya", "Pooja", "Bhavani"]
REVIEWS_EN = {
    5: ["I wait here for my bus after work. The staff keep an eye on the road.", "Bright lights and always people around. Felt very safe.",
        "Akka let me sit inside till my auto came.", "Good place to wait with my daughter in the evening."],
    4: ["Busy till late, the shopkeeper is helpful.", "Well lit, but the pavement outside is broken.",
        "Safe to wait, a little crowded at 8 am."],
    3: ["Okay in the evening, quiet after 9 pm.", "Lighting outside could be better."],
    2: ["Closes early, the street gets empty after that.", "Not many people around at night."],
    1: ["Dark corner at night, I would not wait here alone."],
}
REVIEWS_TA = {
    5: ["இரவிலும் வெளிச்சமாக இருக்கும். பாதுகாப்பாக உணர்ந்தேன்.", "கடைக்காரர் உதவி செய்தார். பஸ் வரும் வரை காத்திருந்தேன்."],
    4: ["கூட்டம் இருக்கும், பாதுகாப்பாக இருக்கிறது.", "நல்ல வெளிச்சம், ஆனால் சாலை மோசம்."],
    3: ["மாலையில் பரவாயில்லை, இரவு 9 மணிக்கு பிறகு அமைதி."],
    2: ["சீக்கிரம் மூடிவிடுவார்கள். பிறகு தெரு காலியாகிவிடும்."],
    1: ["இரவில் இருட்டாக இருக்கும். தனியாக காத்திருக்க மாட்டேன்."],
}
DEMO_USERS = [("u_demo", "Priya", "Nungambakkam", "Anna Nagar West"), ("u_meena", "Meena", "Adyar", "Guindy"),
              ("u_kavitha", "Kavitha", "Velachery", "T. Nagar"), ("u_fathima", "Fathima", "Mylapore", "Egmore"),
              ("u_revathi", "Revathi", "Tambaram", "Guindy"), ("u_anitha", "Anitha", "Kilpauk", "Koyambedu"),
              ("u_divya", "Divya", "Vadapalani", "T. Nagar"), ("u_saranya", "Saranya", "Egmore", "Kilpauk")]
RELATIONS = [("Amma", "அம்மா", "mother"), ("Akka", "அக்கா", "sister"), ("Appa", "அப்பா", "father"),
             ("Thambi", "தம்பி", "brother"), ("Friend", "தோழி", "friend"), ("Colleague", "சக ஊழியர்", "colleague")]


EXTRA_COORDS = {  # existing demo stops that are not area centres
    "Anna Nagar": (13.0850, 80.2101), "Anna Nagar East": (13.0846, 80.2230), "Shenoy Nagar": (13.0790, 80.2250),
    "Park": (13.0810, 80.2730), "Saidapet": (13.0213, 80.2231), "T. Nagar Depot": (13.0418, 80.2341),
}
# Real institutions must not carry sample safety claims: give them generic names.
RENAME_CORE_PLACES = {"Kilpauk Government Hospital": ("Kilpauk Area Hospital (24 h)", "கீழ்ப்பாக்கம் மருத்துவமனை (24 மணி)")}

# ------------------------------------------------------------------ helpers

def _load(name):
    with open(DATA / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)


def _save(name, obj):
    with open(DATA / f"{name}.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _core(rows):
    return [r for r in rows if not r.get("generated")]


def _offset(rng, lat, lng, min_m, max_m):
    d, a = rng.uniform(min_m, max_m), rng.uniform(0, 2 * math.pi)
    return (round(lat + d * math.cos(a) / 110540, 6), round(lng + d * math.sin(a) / (111320 * math.cos(math.radians(lat))), 6))


def _dist_m(a, b):
    return math.hypot((a[0] - b[0]) * 110540, (a[1] - b[1]) * 111320 * math.cos(math.radians(a[0])))


def _code(name, used):
    letters = "".join(w[0] for w in name.upper().replace("-", " ").split())[:3]
    base = (letters + name.upper().replace(" ", ""))[:3]
    code, n = base, 2
    while code in used:
        code, n = f"{base[:2]}{n}", n + 1
    used.add(code)
    return code


def _hhmm(m):
    return f"{m // 60:02d}:{m % 60:02d}"


def crowd_profile(rng, kind, open_m, close_m, open_24h):
    """00-23 crowd levels: busy 8-10 and 17-21, quiet late night, empty when closed."""
    out = {}
    for h in range(24):
        if not open_24h and not (open_m <= h * 60 < close_m):
            level = "empty"
        elif 8 <= h <= 10 or 17 <= h <= 21:
            level = rng.choice(["busy", "busy", "moderate"])
        elif 6 <= h <= 7 or 11 <= h <= 16 or h == 22:
            level = rng.choice(["moderate", "moderate", "quiet"])
        else:
            level = "quiet" if kind in ("hospital", "petrol_bunk", "police_booth", "atm") else rng.choice(["quiet", "empty"])
        out[f"{h:02d}"] = level
    return out


# ------------------------------------------------------------------ build

def build(seed: int = SEED) -> dict:
    rng = random.Random(seed)
    routes_json, metro_json, trains_json = _load("routes"), _load("metro"), _load("trains")
    places_json, transfers_json, areas_json, circle_json = _load("places"), _load("transfers"), _load("areas"), _load("circle")

    used_codes = set()
    for r in _core(routes_json["routes"]):
        used_codes |= {s["code"] for s in r["stops"]}
    for line in _core(metro_json["lines"]) + _core(trains_json["lines"]):
        used_codes |= {s["code"] for s in line["stations"]}
    area_of = {a["name"]: a for a in areas_json["areas"]}

    # ---- stops
    stops, stop_area, stop_xy = {}, {}, {}

    def add_stop(code, name, area, kind, lat, lng):
        if code not in stops:
            stops[code] = {"id": code, "name": name, "name_ta": AREAS.get(area, (0, 0, None))[2] if name == area else None,
                           "area": area, "kind": kind, "lat": lat, "lng": lng, "source": "sample"}
        stop_area[name], stop_xy[name] = area, (lat, lng)

    def area_for_point(lat, lng):
        return min(AREAS, key=lambda a: _dist_m((lat, lng), AREAS[a][:2]))

    core_coords = {a["name"]: (a["lat"], a["lng"]) for a in areas_json["areas"]}
    for a in areas_json["areas"]:
        for alias in a.get("aliases", []):
            core_coords.setdefault(alias.title(), (a["lat"], a["lng"]))
    core_coords.update(EXTRA_COORDS)
    for r in _core(routes_json["routes"]):
        for s in r["stops"]:
            lat, lng = core_coords.get(s["name"]) or core_coords.get(s["name"].replace(" Depot", "")) or AREAS["T Nagar"][:2]
            s["lat"], s["lng"] = lat, lng
            add_stop(s["code"], s["name"], area_for_point(lat, lng), "bus_stop", lat, lng)

    new_bus_stops = {}
    for area, names in NEW_STOPS.items():
        alat, alng, _ = AREAS[area]
        for name in names:
            lat, lng = _offset(rng, alat, alng, 250, 1400)
            code = _code(name, used_codes)
            add_stop(code, name, area, "bus_stop", lat, lng)
            new_bus_stops.setdefault(area, []).append({"name": name, "code": code, "lat": lat, "lng": lng})

    for line in _core(metro_json["lines"]):
        for s in line["stations"]:
            lat, lng = core_coords.get(s["name"], AREAS["Koyambedu"][:2])
            add_stop(s["code"], s["name"], area_for_point(lat, lng), "metro_station", lat, lng)
    for line in _core(trains_json["lines"]):
        for s in line["stations"]:
            lat, lng = core_coords.get(s["name"], AREAS["Egmore"][:2])
            add_stop(s["code"], s["name"], area_for_point(lat, lng), "train_station", lat, lng)

    # ---- generated bus routes
    gen_routes = []
    queues = {a: rng.sample(s, len(s)) for a, s in new_bus_stops.items()}  # cycle so every stop gets a route
    for number, path in NEW_ROUTES:
        seq = []
        for area in path:
            q = queues[area]
            take = [q[i % len(q)] for i in range(2)]
            queues[area] = q[2:] + q[:2]
            seq += take
        minutes, prev = 0, None
        stops_out = []
        for s in seq:
            if prev:
                minutes += max(3, round(_dist_m((prev["lat"], prev["lng"]), (s["lat"], s["lng"])) * 1.3 / 300) + 1)
            stops_out.append({"name": s["name"], "code": s["code"], "min": minutes, "lat": s["lat"], "lng": s["lng"],
                              "area": stop_area[s["name"]]})
            prev = s
        paid = number in PAID_ROUTES
        first = rng.choice(["04:45", "05:00", "05:15", "05:30"])
        gen_routes.append({
            "id": number, "number": number, "mode": "bus",
            "name": f"{stops_out[0]['name']} - {stops_out[-1]['name']}",
            "is_free": not paid, "free_for_women": not paid,
            "fare_inr": rng.choice([25, 30, 40]) if paid else 0, "fare_others_inr": rng.choice([10, 12, 15, 18, 20]),
            "operator": "MTC", "stops": stops_out, "first": first, "last": rng.choice(["21:30", "22:00", "22:30", "23:00"]),
            "frequency_minutes": rng.choice([8, 10, 12, 15, 20]), "walk_start_min": rng.choice([2, 3, 4]),
            "walk_end_min": rng.choice([2, 3]), "stops_well_lit": rng.random() < 0.7,
            "notes": "AC deluxe, paid" if paid else "Ordinary bus, free for women",
            "source": "sample", "generated": True,
        })
    routes_json["routes"] = _core(routes_json["routes"]) + gen_routes

    # ---- generated metro + train lines
    blue = {"id": "M-BLUE", "name": "Blue Line (sample)", "color": "#1F5BDA", "first": "05:00", "last": "23:00",
            "headway_peak_min": 5, "headway_offpeak_min": 9, "peak_hours": ["07:30-10:30", "17:00-20:30"],
            "women_coach": "First coach (front of the train)", "stations": [], "source": "sample", "generated": True}
    for name, area, minutes in BLUE_LINE:
        lat, lng = _offset(rng, *AREAS[area][:2], 150, 900)
        code = _code(name, used_codes)
        add_stop(code, name, area, "metro_station", lat, lng)
        blue["stations"].append({"name": name, "code": code, "min": minutes, "area": area, "platform": rng.choice(["1", "2"]),
                                 "best_exit": f"Exit {rng.choice('ABCD')} - {rng.choice(STREETS)}"})
    metro_json["lines"] = _core(metro_json["lines"]) + [blue]

    mrts = {"id": "T-MRTS", "name": "Beach - Velachery MRTS (sample)", "fare_inr": 5, "fare_first_class_inr": 40,
            "ladies_coaches": [{"position": "front", "coach_numbers": [1], "note": "Ladies coach behind the engine"}],
            "total_coaches": 6, "ladies_special": [], "first": "04:30", "last_train": "23:15", "frequency_minutes": 15,
            "delays_sample": {}, "stations": [], "source": "sample", "generated": True}
    for name, area, minutes in MRTS_LINE:
        lat, lng = _offset(rng, *AREAS[area][:2], 150, 900)
        code = _code(name, used_codes)
        add_stop(code, name, area, "train_station", lat, lng)
        mrts["stations"].append({"name": name, "code": code, "min": minutes, "area": area, "platform": "1"})
    trains_json["lines"] = _core(trains_json["lines"]) + [mrts]

    # ---- transfers
    name_to_code = {s["name"]: c for c, s in stops.items()}
    gen_transfers = [{"at": at, "code": name_to_code[at], "from": f, "to": t, "walk_min": w, "lit": lit, "note": note,
                      "source": "sample", "generated": True} for at, f, t, w, lit, note in TRANSFER_SPOTS]
    transfers_json["transfers"] = _core(transfers_json["transfers"]) + gen_transfers

    # ---- areas.json: add the new areas once
    for row in NEW_AREA_ROWS:
        if row["name"] not in area_of:
            areas_json["areas"].append(row)

    # ---- places (~20 per area). Kept away from the demo stops so the demo ranking is unchanged.
    core_places = _core(places_json["places"])
    for p in core_places:
        if p["name"] in RENAME_CORE_PLACES:
            p["name"], p["name_ta"] = RENAME_CORE_PLACES[p["name"]]
    for p in core_places:  # sample reviews: first name + "(sample)"
        for r in p.get("reviews", []):
            if not r["author"].endswith("(sample)"):
                r["author"] += " (sample)"
    demo_points = [(p["lat"], p["lng"]) for p in core_places]
    names_used = {p["name"] for p in core_places}
    gen_places, n = [], 100
    for area, (alat, alng, _ta) in AREAS.items():
        area_stops = new_bus_stops[area]
        for _ in range(20):
            kind = rng.choices(PLACE_TYPES, TYPE_WEIGHTS)[0]
            for _try in range(20):
                lat, lng = _offset(rng, alat, alng, 300, 1500)
                if all(_dist_m((lat, lng), d) > 300 for d in demo_points):
                    break
            near = min(area_stops, key=lambda s: _dist_m((lat, lng), (s["lat"], s["lng"])))
            pre, suf = NAME_PARTS[kind]
            street = rng.choice(STREETS)
            if kind in ("atm", "police_booth", "petrol_bunk", "bus_shelter"):
                name = f"{pre[0]}, {near['name']}"
            else:
                name = f"{rng.choice(pre)} {rng.choice(suf)}".strip()
            if name in names_used:
                name = f"{name}, {area}"
            k = 2
            while name in names_used:
                name, k = f"{name.split(' #')[0]} #{k}", k + 1
            names_used.add(name)
            open_24h = kind in ("atm", "hospital", "police_booth", "bus_shelter") or (kind in ("pharmacy", "petrol_bunk") and rng.random() < 0.35)
            open_m = 0 if open_24h else {"tea_shop": 330, "shg_kiosk": 360, "grocery": 420, "pharmacy": 480, "petrol_bunk": 360}[kind] + rng.choice([0, 30])
            close_m = 24 * 60 - 1 if open_24h else {"tea_shop": 1350, "shg_kiosk": 1290, "grocery": 1290, "pharmacy": 1320, "petrol_bunk": 1380}[kind] + rng.choice([-30, 0, 30])
            women_run = kind == "shg_kiosk" or rng.random() < {"grocery": .35, "tea_shop": .2, "pharmacy": .25}.get(kind, .03)
            well_lit = rng.random() < (0.6 if kind == "bus_shelter" else 0.78)
            gen_places.append({
                "id": f"p{n}", "name": name, "name_ta": None, "type": kind, "category": CATEGORY[kind],
                "address": f"{street}, {area}", "area": area, "near_stop": near["code"], "lat": lat, "lng": lng,
                "open": _hhmm(open_m), "close": _hhmm(min(close_m, 1439)), "open_24h": open_24h,
                "women_run": women_run, "well_lit": well_lit, "can_wait_inside": kind in ("pharmacy", "grocery", "hospital", "shg_kiosk") and rng.random() < .7,
                "crowd_by_hour": crowd_profile(rng, kind, open_m, close_m, open_24h),
                "rating": None, "reviews_count": 0, "photo": None, "phone": None, "reviews": [],
                "source": "sample", "generated": True,
            })
            n += 1
    for p in core_places:
        p.setdefault("area", stops.get(p["near_stop"], {}).get("area") or area_for_point(p["lat"], p["lng"]))
        p.setdefault("phone", None)

    # ---- reviews (~200 total incl. the hand-written ones)
    existing = sum(len(p.get("reviews", [])) for p in core_places)
    for _ in range(200 - existing):
        p = rng.choice(gen_places)
        score = 2 + p["women_run"] + p["well_lit"] + (p["open_24h"] or p["close"] >= "22:00")
        rating = max(1, min(5, round(rng.gauss(score, 0.8))))
        lang = "ta" if rng.random() < 0.35 else "en"
        text = rng.choice((REVIEWS_TA if lang == "ta" else REVIEWS_EN)[rating])
        p["reviews"].append({"author": f"{rng.choice(FIRST_NAMES)} (sample)", "rating": rating, "days_ago": rng.randint(1, 120),
                             "lang": lang, "text": text})
    for p in gen_places:
        if p["reviews"]:
            p["rating"] = round(sum(r["rating"] for r in p["reviews"]) / len(p["reviews"]), 1)
            p["reviews_count"] = len(p["reviews"]) + rng.randint(0, 40)
    places_json["places"] = core_places + gen_places

    # ---- users + circle (fake phones only)
    demo_user = next(u for u in circle_json["users"] if u["user_id"] == "u_demo")
    for i, c in enumerate(demo_user["contacts"], start=1):
        c["phone"] = f"+910000000{i:03d}"
        c["phone_masked"] = f"+91 ••••• •••{i:02d}"
    users = [demo_user]
    for uid, name, home, start in DEMO_USERS[1:]:
        contacts = []
        for j in range(rng.randint(2, 5)):
            label, label_ta, rel = RELATIONS[j % len(RELATIONS)]
            num = len(users) * 10 + j + 1
            contacts.append({"id": f"{uid}_c{j + 1}", "label": label, "label_ta": label_ta, "relation": rel,
                             "phone": f"+910000000{num:03d}", "phone_masked": f"+91 ••••• •••{num % 100:02d}",
                             "accepted": rng.random() < 0.8, "status": "available", "area": home,
                             "lat": None, "lng": None, "source": "sample"})
        users.append({"user_id": uid, "display_name": name, "home_area": home, "start_area": start,
                      "home": dict(zip(("lat", "lng"), AREAS.get(home, AREAS["T Nagar"])[:2])),
                      "contacts": contacts, "saved_places": [], "source": "sample"})
    circle_json["users"] = users

    # ---- past trips + events (Supabase only)
    trips, events = [], []
    bus_routes = [r for r in routes_json["routes"]]
    for i in range(60):
        u = rng.choice(users)
        r = rng.choice(bus_routes)
        a, b = sorted(rng.sample(range(len(r["stops"])), 2))
        day = rng.randint(1, 30)
        start_m = rng.choice(list(range(6 * 60, 23 * 60, 7)))
        ride = r["stops"][b]["min"] - r["stops"][a]["min"] + 5
        status = rng.choices(["reached", "alerted", "active", "stopped"], [42, 8, 4, 6])[0]
        start_iso = f"2026-09-{day:02d}T{_hhmm(start_m)}:00+05:30"
        eta_m = start_m + ride
        eta_iso = f"2026-09-{day:02d}T{_hhmm(min(eta_m, 1439))}:00+05:30"
        tid = f"t_sample_{i + 1:03d}"
        trips.append({"id": tid, "user_id": u["user_id"], "option_id": f"bus:{r['id']}:{r['stops'][a]['code']}", "kind": "bus",
                      "summary": f"{r['number']} {r['stops'][a]['name']} -> {r['stops'][b]['name']}",
                      "from_area": stop_area.get(r["stops"][a]["name"]), "to_area": stop_area.get(r["stops"][b]["name"]),
                      "alight_stop": r["stops"][b]["code"], "start_at": start_iso, "eta_at": eta_iso, "status": status,
                      "notified_circle": rng.random() < 0.7, "reminded": status in ("alerted", "reached") and rng.random() < .4,
                      "distance_m": None, "source": "sample"})
        seq = ["start"] + (["checkin"] if rng.random() < .5 else []) + \
              {"reached": ["reached"], "alerted": ["reminder", "alert"], "stopped": ["stop"], "active": []}[status]
        for k, ev in enumerate(seq):
            events.append({"trip_id": tid, "at": f"2026-09-{day:02d}T{_hhmm(min(start_m + k * max(3, ride // max(1, len(seq))), 1439))}:00+05:30",
                           "event": ev, "detail": {"sample": True}, "source": "sample"})

    # ---- anonymous request log (Supabase only)
    hours = list(range(24))
    hour_w = [1, 1, 1, 1, 1, 2, 5, 9, 12, 10, 6, 5, 5, 5, 5, 6, 8, 11, 12, 11, 9, 7, 4, 2]
    request_log = []
    for _ in range(300):
        request_log.append({
            "area": rng.choice(list(AREAS)), "hour": rng.choices(hours, hour_w)[0],
            "mode": rng.choices(["bus", "metro", "train", "auto", "walk"], [55, 18, 10, 12, 5])[0],
            "lang": rng.choices(["ta", "en", "tanglish"], [45, 30, 25])[0],
            "channel": rng.choices(["sms", "app", "voice"], [50, 35, 15])[0],
            "intent": rng.choices(["plan_trip", "safe_route_home", "places_open_now", "free_bus_now", "start_trip", "reached", "sos"],
                                  [45, 15, 12, 10, 8, 8, 2])[0],
            "route_found": rng.random() < 0.85, "safe_place_found": rng.random() < 0.75, "source": "sample",
        })

    return {"routes_json": routes_json, "metro_json": metro_json, "trains_json": trains_json,
            "places_json": places_json, "transfers_json": transfers_json, "areas_json": areas_json,
            "circle_json": circle_json, "stops": list(stops.values()), "trips": trips, "trip_events": events,
            "request_log": request_log}


def write_app_json(b: dict):
    for name in ("routes", "metro", "trains", "places", "transfers", "areas", "circle"):
        _save(name, b[f"{name}_json"])


def counts(b: dict) -> dict:
    reviews = sum(len(p.get("reviews", [])) for p in b["places_json"]["places"])
    routes = len(b["routes_json"]["routes"]) + len(b["metro_json"]["lines"]) + len(b["trains_json"]["lines"]) + 1  # + auto rule
    users = b["circle_json"]["users"]
    return {"stops": len(b["stops"]), "routes": routes, "transfers": len(b["transfers_json"]["transfers"]),
            "places": len(b["places_json"]["places"]), "reviews": reviews, "users": len(users),
            "circle_contacts": sum(len(u["contacts"]) for u in users), "trips": len(b["trips"]),
            "trip_events": len(b["trip_events"]), "request_log": len(b["request_log"])}


if __name__ == "__main__":
    data = build()
    write_app_json(data)
    c = counts(data)
    for k, v in c.items():
        print(f"  {k:<16} {v}")
    print(f"  {'TOTAL':<16} {sum(c.values())}")
