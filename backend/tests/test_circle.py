from datetime import timedelta

from backend.agents import circle, route, sms
from backend.tests.conftest import at


def bus_option():
    return next(o for o in route.plan("Anna Nagar West", "Nungambakkam", "08:00")["options"] if o["id"] == "bus:MTC-18683:MTC9835")  # real 40H


def test_circle_never_returns_phone():
    circle.add_contact("u_demo", "Meera", "+915000000099", confirmed=True)
    for c in circle.list_circle("u_demo")["contacts"]:
        assert "phone" not in c


def test_max_five_contacts():
    circle.add_contact("u_demo", "One", confirmed=True)  # 5th
    assert circle.add_contact("u_demo", "Six", confirmed=True)["error"] == "circle_full"


def test_invite_needs_confirmation():
    r = circle.add_contact("u_demo", "Meera", "+915000000099")
    assert r["needs_confirmation"] and r["action"] == "invite"
    assert not sms.OUTBOX


def test_accept_and_remove():
    cid = circle.add_contact("u_new", "Meera", confirmed=True)["contact"]["id"]
    assert circle.accept_contact("u_new", cid)["contact"]["accepted"] is True
    assert circle.remove_contact("u_new", cid)["removed"] is True


def test_start_trip_needs_confirmation_to_message_circle():
    r = circle.start_trip("u_demo", bus_option(), "Anna Nagar West", "Nungambakkam", now=at("08:00"))
    assert r["needs_confirmation"] and "Amma" in r["to"]
    assert not circle.STORE.trips and not sms.OUTBOX


def test_journey_watch_reminder_then_alert():
    r = circle.start_trip("u_demo", bus_option(), "Anna Nagar West", "Nungambakkam", confirmed=True,
                          user_phone="+15005550008", now=at("08:00"))
    trip = r["trip"]
    assert r["delivery"]["demo_logged"] == 3 and r["delivery"]["sent"] == 0  # honest: not really sent
    assert trip["eta_hhmm"] == "08:39"  # 40H leaves Anna Nagar West Depot 08:20, 17 min ride + walks
    assert circle.tick(at("08:30")) == []
    acts = circle.tick(at("08:39"))
    assert acts[0]["action"] == "reminder"
    acts = circle.tick(at("08:49"))
    assert acts[0]["action"] == "alert"
    assert circle.STORE.trips[trip["trip_id"]]["status"] == "alerted"
    assert circle.tick(at("09:30")) == []  # alert only once


def test_reached_stops_watch_and_location():
    trip = circle.start_trip("u_demo", bus_option(), "Anna Nagar West", "Nungambakkam", confirmed=True, now=at("08:00"))["trip"]
    circle.checkin(trip["trip_id"], lat=13.07, lng=80.22, now=at("08:10"))
    res = circle.reached(trip["trip_id"], now=at("08:40"))
    assert res["trip"]["status"] == "reached" and res["trip"]["last_location"] is None
    assert circle.tick(at("09:30")) == []


def test_location_only_stored_during_active_trip():
    trip = circle.start_trip("u_demo", bus_option(), "A", "B", confirmed=True, now=at("08:00"))["trip"]
    assert circle.checkin(trip["trip_id"], lat=13.07, lng=80.22, now=at("08:05"))["location_stored"] is True
    circle.reached(trip["trip_id"], now=at("08:30"))
    after = circle.checkin(trip["trip_id"], lat=13.08, lng=80.23, now=at("08:35"))
    assert after["location_stored"] is False and after["trip"]["last_location"] is None


def test_sos_skips_confirmation_and_is_honest():
    r = circle.sos("u_demo", 13.0604, 80.2422, now=at("21:40"))
    assert r["confirmation_skipped"] and r["sos"]["active"]
    assert r["delivery"]["sent"] == 0 and r["delivery"]["demo_logged"] == 3
    assert {h["number"] for h in r["helplines"]} == {"112", "181", "1091", "100"}
    assert r["nearest_help"]
    stop = circle.sos_stop("u_demo", now=at("21:50"))
    assert stop["sos"]["active"] is False and stop["sos"]["location"] is None


def test_sms_user_id_is_pseudonymous():
    uid = circle.user_id_for_phone("+915000011111")
    assert uid.startswith("u_") and "50000" not in uid


def test_message_contact_needs_confirmation_and_is_honest():
    r = circle.message_contact("u_demo", "c2", "meet", "Main road")
    assert r["needs_confirmation"] and "Main road" in r["preview"] and not sms.OUTBOX
    r = circle.message_contact("u_demo", "c2", "meet", "Main road", confirmed=True)
    assert r["status"] == "mock_logged" and r["delivery"]["sent"] == 0
    assert circle.message_contact("u_demo", "c4", confirmed=True)["error"] == "not_in_circle"  # pending invite
    assert circle.message_contact("u_demo", "c2", "free text", confirmed=True)["error"] == "unknown_message"


def test_sos_nearest_help_uses_trip_area_without_gps():
    opt, _ = route.find_option(None, None, "21:40", "walk:w-nmb-main")
    circle.start_trip("u_demo", opt, "Nungambakkam", "Nungambakkam", confirmed=True, now=at("21:40"))
    r = circle.sos("u_demo", now=at("21:45"))
    assert r["nearest_help"] and all(h["distance_m"] <= 1500 for h in r["nearest_help"])
    assert r["nearest_help"][0]["name"] in {"Nungambakkam 24h Pharmacy", "Lakshmi Tea Stall (SHG)", "ATM - High Road", "Petrol Bunk, High Road"}
