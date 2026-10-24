from backend.agents import places, route


def test_search_near_default_point():
    res = places.search(time="21:00")
    assert res["count"] >= 3 and res["source"] == "sample"
    assert all("distance_m" in p for p in res["places"])


def test_open_now_filter():
    res = places.search(lat=13.0604, lng=80.2422, open_now=True, time="21:40")
    assert res["places"] and all(p["open_now"] for p in res["places"])
    assert "p15" not in {p["id"] for p in res["places"]}  # Sundari Stores closes 20:00


def test_type_and_chip_filters():
    assert all(p["type"] == "pharmacy" for p in places.search(type="pharmacy", radius_m=50000)["places"])
    assert all(p["women_run"] for p in places.search(chip="women_run", radius_m=50000)["places"])
    help_types = {p["type"] for p in places.search(chip="help", radius_m=50000)["places"]}
    assert help_types <= {"police_booth", "hospital"}


def test_along_route():
    opt = next(o for o in route.plan("Anna Nagar West", "Nungambakkam", "08:00")["options"] if o["kind"] == "bus")
    stops = {p["near_stop"] for p in places.along_route(opt, time="08:00")["places"]}
    assert stops <= {"ANW", "NMB"} and stops


def test_details_with_reviews_and_night_safety():
    d = places.details("p1", time="21:00")
    assert d["name"] == "Lakshmi SHG Kiosk" and d["open_now"]
    assert d["reviews"] and d["night_safety"]["label"] == "Very good"
    assert d["closes_label"] == "Closes 11 pm"
    assert places.details("nope")["error"] == "not_found"


def test_find_by_name():
    assert places.find_by_name("is Lakshmi SHG kiosk open") == "p1"
    assert places.find_by_name("Rose Bakery") == "p13"
    assert places.find_by_name("random words") is None


def test_near_stop_name():
    assert places.details("p1")["near_stop_name"] == "Anna Nagar West"
    assert places.details("p16")["near_stop_name"] == "Koyambedu"
