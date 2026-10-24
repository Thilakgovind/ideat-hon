from backend import data
from backend.agents import route


def test_match_place_variants():
    assert route.match_place("T Nagar") == "T. Nagar"  # never Thirumangalam
    assert route.match_place("nungambakkam bus") == "Nungambakkam"
    assert route.match_place("Anna Nagar W") == "Anna Nagar West"
    assert route.match_place("நுங்கம்பாக்கம்") == "Nungambakkam"
    assert route.match_place("kilpak") == "Kilpauk"
    assert route.match_place("Fake Nagar") is None
    assert route.match_place("") is None


def test_demo_route_has_bus_metro_and_auto():
    plan = route.plan("Anna Nagar West", "Nungambakkam", "08:00")
    kinds = {o["kind"] for o in plan["options"]}
    assert {"bus", "bus+metro", "auto"} <= kinds
    bus = next(o for o in plan["options"] if o["kind"] == "bus")
    assert bus["legs"][1]["label"] == "21G"
    assert bus["is_free"] and bus["fare_inr"] == 0
    assert bus["total_min"] == 35  # walk 3 + bus 30 + walk 2
    assert bus["next"][0] == "08:12"


def test_bus_metro_fare_and_switch():
    plan = route.plan("Anna Nagar West", "Nungambakkam", "08:00")
    o = next(o for o in plan["options"] if o["kind"] == "bus+metro")
    assert o["fare_inr"] == 30 and o["switches"] == 1
    assert o["switch_info"]["at"] == "Koyambedu" and o["switch_info"]["lit"] is True
    metro = next(l for l in o["legs"] if l["mode"] == "metro")
    assert metro["women_coach"] and metro["best_exit"]


def test_auto_is_estimate_with_night_fare():
    day = next(o for o in route.plan("Anna Nagar West", "Nungambakkam", "12:00")["options"] if o["kind"] == "auto")
    night = next(o for o in route.plan("Anna Nagar West", "Nungambakkam", "23:30")["options"] if o["kind"] == "auto")
    assert day["fare_is_estimate"] and night["night_fare"] and night["fare_inr"] > day["fare_inr"]
    assert "Namma Yatri" in day["booking_links"]


def test_late_night_buses_not_offered():
    plan = route.plan("Anna Nagar West", "Nungambakkam", "23:30")
    assert "21G" in plan["not_running_now"]
    assert all(o["kind"] != "bus" for o in plan["options"])


def test_train_option_with_ladies_coach():
    plan = route.plan("Chetpet", "Nungambakkam", "21:00")
    train = next(o for o in plan["options"] if o["kind"] == "train")
    leg = next(l for l in train["legs"] if l["mode"] == "train")
    assert leg["ladies_coaches"] and leg["last_train"] == "23:55"


def test_wrong_direction_and_unknown():
    assert all(o["kind"] == "auto" for o in route.plan("Nungambakkam", "Anna Nagar West", "08:00")["options"])
    assert route.plan("Fake Nagar", "Nungambakkam")["error"] == "no_match"
    assert route.plan("Kilpauk", "kilpauk")["error"] == "same_place"


def test_arrivals_free_only():
    arr = route.arrivals("Anna Nagar West", "08:00", free_only=True)
    assert arr["arrivals"] and all(a["is_free"] for a in arr["arrivals"])
    assert arr["arrivals"] == sorted(arr["arrivals"], key=lambda a: a["in_min"])


def test_every_option_is_from_data():
    known = {r["id"] for r in data.routes()} | {l["id"] for l in data.metro()["lines"]} | {l["id"] for l in data.trains()}
    for o in route.plan("Anna Nagar West", "Nungambakkam", "08:00")["options"]:
        for leg in o["legs"]:
            if leg["mode"] in ("bus", "metro", "train"):
                assert leg["route_id"] in known
        assert o["source"] == "sample"


def test_find_option_replans_on_server():
    opt, _ = route.find_option("Anna Nagar West", "Nungambakkam", "08:00", "bus:21G:ANW")
    assert opt and opt["fare_inr"] == 0
    assert route.find_option("Anna Nagar West", "Nungambakkam", "08:00", "bus:FAKE:ANW")[0] is None
