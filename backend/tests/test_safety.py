from backend import data
from backend.agents import circle, route, safety


def place(**kw):
    base = {"id": "x", "name": "X", "type": "tea_shop", "category": "Tea", "open": "06:00", "close": "22:00",
            "open_24h": False, "women_run": False, "well_lit": False, "crowd_by_hour": {"06": "quiet"}}
    base.update(kw)
    return base


def test_place_score_rules():
    m21 = 21 * 60
    assert safety.place_score(place(), m21) == 3  # open only
    assert safety.place_score(place(women_run=True), m21) == 5
    assert safety.place_score(place(well_lit=True), m21) == 5  # lit counts after 6pm
    assert safety.place_score(place(well_lit=True), 10 * 60) == 3  # not in the day
    assert safety.place_score(place(crowd_by_hour={"06": "busy"}), m21) == 5
    assert safety.place_score(place(crowd_by_hour={"06": "empty"}), m21) == 1  # empty after 7pm -2
    assert safety.place_score(place(open_24h=True), 3 * 60) == 4
    assert safety.place_score(place(close="20:00"), m21) == 0  # closed


def test_score_ignores_non_neutral_fields():
    """Profiling fields must never change a score."""
    p = place(women_run=True)
    profiled = dict(p, crowd_type="students", community="any", income="low")
    assert safety.place_score(p, 1200) == safety.place_score(profiled, 1200)


def test_open_overnight_hours():
    assert safety.is_open(place(open="18:00", close="02:00"), 60)
    assert not safety.is_open(place(open="18:00", close="02:00"), 12 * 60)


def test_rank_options_safest_cheapest_fastest():
    plan = route.plan("Anna Nagar West", "Nungambakkam", "08:00")
    safest = safety.rank_options(plan["options"], 480, "safest")
    assert safest[0]["kind"] == "bus" and "SAFEST" in safest[0]["badges"]
    assert safest[0]["safe_wait"]["name"] == "Lakshmi SHG Kiosk"
    assert "No switches" in safest[0]["safety_tags"]
    assert safety.rank_options(plan["options"], 480, "cheapest")[0]["fare_inr"] == 0
    fastest = safety.rank_options(plan["options"], 480, "fastest")
    assert fastest[0]["total_min"] == min(o["total_min"] for o in fastest)


def test_child_penalises_switches():
    plan = route.plan("Anna Nagar West", "Nungambakkam", "08:00")
    o = next(o for o in plan["options"] if o["switches"] == 1)
    assert safety.score_option(o, 480, with_child=True)["safety_score"] < safety.score_option(o, 480)["safety_score"]


def test_safe_way_home_main_road_wins_at_night():
    contacts = circle.STORE.user("u_demo")["contacts"]
    res = safety.compare_walk_paths("NMB", 21 * 60 + 40, contacts)
    main, lane = res["paths"]
    assert main["name"] == "Main road" and main["badge"] == "SAFEST"
    assert main["people_label"] == "Busy" and main["shops_open"] == 6
    assert [p["label"] for p in main["your_people"]] == ["Kavya"]
    assert lane["shops_open"] == 0 and lane["people_around"] in ("quiet", "empty")
    assert [p["label"] for p in res["at_destination"]] == ["Amma"]


def test_pending_contacts_never_shown_on_map():
    contacts = [{"id": "z", "label": "Z", "accepted": False, "lat": 13.0610, "lng": 80.2424, "status": "nearby"}]
    res = safety.compare_walk_paths("NMB", 21 * 60, contacts)
    assert all(not p["your_people"] for p in res["paths"])


def test_night_safety_label():
    lakshmi = next(p for p in data.places() if p["id"] == "p1")
    ns = safety.night_safety(lakshmi)
    assert ns["label"] == "Very good" and "Women-run" in ns["tags"] and "Can wait inside" in ns["tags"]
