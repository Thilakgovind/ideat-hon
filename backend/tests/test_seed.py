"""Sample data generator + Supabase seeder (no network)."""
import json
import re

from backend import config
from backend.seed import generate_sample
from backend.seed_supabase import ORDER, REPLACE_SAMPLE, rows_from, seed

B = generate_sample.build()
ROWS = rows_from(B)
FAKE = re.compile(r"^\+910000000\d{3}$")


def test_deterministic():
    again = generate_sample.build()
    assert json.dumps(again, sort_keys=True, default=str) == json.dumps(B, sort_keys=True, default=str)


def test_seed_counts():
    c = {t: len(ROWS[t]) for t in ORDER}
    assert c["places"] >= 250 and c["reviews"] == 200 and c["users"] == 8
    assert c["trips"] == 60 and c["request_log"] == 300 and c["transfers"] == 20
    assert c["routes"] >= 25 and c["stops"] >= 60 and 8 <= c["circle_contacts"] <= 40
    assert sum(c.values()) >= 650


def test_every_row_is_sample_or_labelled_real():
    for t in ORDER:
        for r in ROWS[t]:
            assert r["source"] == "sample" or (t in ("routes", "stops") and r["source"] == "live"
                                                and r["data_source"] == "ChennaiGTFS (MTC)"), t


def test_real_routes_seeded_with_timetables():
    real = [r for r in ROWS["routes"] if r["source"] == "live"]
    stop_ids = {s["id"] for s in ROWS["stops"]}
    assert any(r["number"] == "40H" for r in real)
    for r in real:
        assert r["one_way"] and r["departures"] and "white-board" in r["free_note"]
        assert all(s["stop_id"] in stop_ids for s in r["stop_sequence"])  # every stop exists (FK-safe)
    assert all(s["area"] for s in ROWS["stops"])  # stops.area is NOT NULL


def test_no_phones_outside_private_tables():
    assert all(p["phone"] is None for p in ROWS["places"])
    for t in ORDER:
        if t in ("circle_contacts", "users"):
            continue
        assert not re.search(r"\+91\d{10}|\b[6-9]\d{9}\b", json.dumps(ROWS[t], ensure_ascii=False)), t
    assert all(FAKE.match(c["phone"]) for c in ROWS["circle_contacts"])
    assert all(u["phone"] is None for u in ROWS["users"])


def test_request_log_is_anonymous():
    allowed = {"area", "hour", "mode", "lang", "channel", "intent", "route_found", "safe_place_found", "source"}
    assert all(set(r) <= allowed for r in ROWS["request_log"])


def test_reviewers_first_name_sample_only():
    assert all(re.fullmatch(r"[A-Z][a-z]+ \(sample\)", r["author"]) for r in ROWS["reviews"])


def test_demo_contact_override_only_in_supabase_rows(monkeypatch):
    monkeypatch.setenv("DEMO_CONTACT_PHONE_1", "+15005550006")
    rows = rows_from(generate_sample.build())
    priya = [c for c in rows["circle_contacts"] if c["user_id"] == "u_demo"]
    assert priya[0]["phone"] == "+15005550006" and FAKE.match(priya[1]["phone"])
    assert "+15005550006" not in (config.DATA_DIR / "circle.json").read_text(encoding="utf-8")


def test_crowd_profiles_realistic():
    gen = [p for p in B["places_json"]["places"] if p.get("generated")]
    for p in gen:
        assert len(p["crowd_by_hour"]) == 24
    busy = sum(p["crowd_by_hour"]["09"] == "busy" for p in gen if p["open_24h"] or p["open"] <= "09:00")
    late = sum(p["crowd_by_hour"]["03"] == "busy" for p in gen)
    assert busy > len(gen) / 3 and late == 0


def test_demo_route_unchanged():
    from backend.agents import route
    ids = [o["id"] for o in route.plan("Anna Nagar West", "Nungambakkam", "08:00")["options"]]
    assert {"bus:MTC-18683:MTC9835", "bus+metro:70:M-PURPLE:ANW", "auto"} <= set(ids)
    assert not any(":21G:" in i for i in ids)  # the old sample 21G is gone; real buses come from ChennaiGTFS


def test_new_areas_reachable():
    from backend.agents import route
    kinds = {o["kind"] for o in route.plan("Mylapore", "Adyar", "09:00")["options"]}
    assert "bus" in kinds and "train" in kinds


class FakeRest:
    def __init__(self):
        self.calls, self.store = [], {}

    def upsert(self, table, rows):
        self.calls.append(("upsert", table))
        self.store.setdefault(table, {}).update({r["id"]: r for r in rows})

    def replace_sample(self, table, rows):
        self.calls.append(("replace", table))
        self.store[table] = {i: r for i, r in enumerate(rows)}

    def count(self, table):
        return len(self.store.get(table, {}))


def test_seed_order_and_rerun_is_idempotent():
    fake = FakeRest()
    first = seed(fake)
    second = seed(fake)
    assert first == second == {t: len(ROWS[t]) for t in ORDER}
    assert [t for _, t in fake.calls[:len(ORDER)]] == ORDER
    assert {t for op, t in fake.calls if op == "replace"} == REPLACE_SAMPLE
