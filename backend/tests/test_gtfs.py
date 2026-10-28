"""Real MTC buses from ChennaiGTFS (data/gtfs_bus.json): honest, sane, one-way timetables."""
from backend import data
from backend.agents import route
from backend.seed import import_gtfs


def test_gtfs_rows_are_real_and_labelled():
    rows = data.gtfs_buses()
    assert rows and all(r["source"] == "ChennaiGTFS (MTC)" and r["one_way"] for r in rows)
    for r in rows:
        assert r["departures"] == sorted(r["departures"]) and r["first"] == r["departures"][0]
        mins = [s["min"] for s in r["stops"]]
        assert mins[0] == 0 and mins == sorted(mins)
        assert r["free_for_women"] and "white-board" in r["free_note"]  # free only on ordinary buses: say so


def test_one_way_rows_are_not_reversed():
    # 40H towards Pattabiram must never be offered for Anna Nagar West -> Nungambakkam
    opts = route.plan("Anna Nagar West", "Nungambakkam", "08:00")["options"]
    ids = {o["id"].split(":")[1] for o in opts if o["kind"] == "bus"}
    assert "MTC-18683" in ids and "MTC-18641" not in ids


def test_departures_come_from_timetable():
    opt = next(o for o in route.plan("Anna Nagar West", "Nungambakkam", "08:00")["options"] if o["id"] == "bus:MTC-18683:MTC9835")
    assert opt["next"] == ["08:20", "08:40", "09:00"] and opt["source"] == "ChennaiGTFS (MTC)"


def test_tag_areas_prefers_names_and_skips_misplaced_stops():
    areas = [{"name": "Nungambakkam", "lat": 13.0604, "lng": 80.2422}, {"name": "Anna Nagar West", "lat": 13.0878, "lng": 80.2006}]
    stops = [
        {"name": "Nungambakkam", "lat": 13.0838, "lng": 80.2087},  # feed error: named Nungambakkam, sits in Anna Nagar
        {"name": "Anna Nagar West Depot", "lat": 13.0937, "lng": 80.1984},
        {"name": "Nungambakkam Railway Station", "lat": 13.0666, "lng": 80.2315},
    ]
    import_gtfs.tag_areas(stops, areas)
    assert stops[0].get("area") is None
    assert stops[1]["area"] == "Anna Nagar West" and stops[2]["area"] == "Nungambakkam"


def test_real_routes_round_trip_through_supabase(monkeypatch):
    """Seeded rows -> Supabase -> store.load_public -> same 40H plan, no duplicate routes."""
    from backend import store
    from backend.seed.generate_sample import build
    from backend.seed_supabase import rows_from
    from backend.tests.conftest import FakeResponse

    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "k")
    rows = rows_from(build())  # times already HH:MM:SS, as Postgres returns them

    def fake_get(url, **kw):
        if kw.get("params", {}).get("limit") == 1:
            return FakeResponse(200, [{"id": "x"}])
        table = url.rsplit("/", 1)[-1]
        start = int(kw["headers"]["Range"].split("-")[0])
        return FakeResponse(200, rows[table][start:start + 1000])
    monkeypatch.setattr(store.httpx, "get", fake_get)
    assert store.load_public()["routes"] == len(rows["routes"])

    ids = [r["id"] for r in data.routes()]
    assert len(ids) == len(set(ids))  # Supabase copy + gtfs_bus.json never doubled
    opt = next(o for o in route.plan("Anna Nagar West", "Nungambakkam", "08:00")["options"] if o["id"] == "bus:MTC-18683:MTC9835")
    assert opt["next"][:2] == ["08:20", "08:40"] and opt["source"] == "ChennaiGTFS (MTC)"
    assert "white-board" in opt["legs"][1]["free_note"]
