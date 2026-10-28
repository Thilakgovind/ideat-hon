from backend import orchestrator
from backend.tests.conftest import at
from backend.tests.helpers import REAL_BUSES, sms_bus


def test_demo_chat_route_card_and_steps():
    r = orchestrator.handle("Nungambakkam, 8am, with my daughter", now=at("07:50"))
    assert r["card"]["type"] == "route" and r["card"]["option"]["kind"] == "bus"
    assert r["card"]["option"]["safe_wait"]["name"] == "Lakshmi SHG Kiosk"
    steps = [s["text"] for s in r["steps"]]
    assert steps[0] == "Understood your request"
    assert steps[1] == "Compared bus, metro and auto"
    assert steps[2].startswith("Ranked") and steps[3] == "Amma will get your trip when you start"
    assert r["steps"][3]["status"] == "pending"
    assert [a["id"] for a in r["actions"]] == ["start_trip", "choose_option"]
    assert r["actions"][1]["label"] == "Metro instead"
    assert r["sample_data"] is True


def test_tamil_reply_for_tamil_request():
    r = orchestrator.handle("நுங்கம்பாக்கம், 8 மணி, பொண்ணோட")
    assert r["reply"]["lang"] == "ta" and "இலவசம்" in r["reply"]["text"]
    assert r["steps"][0]["text"] == "Understood your Tamil request"


def test_sms_reply_fits_and_has_start():
    r = orchestrator.handle("nungambakkam bus 8am", channel="sms", user_id="u_sms")
    assert len(r["sms_text"]) <= 160 and sms_bus(r["sms_text"]) in REAL_BUSES and "START" in r["sms_text"]


def test_sms_after_last_bus_offers_auto():
    r = orchestrator.handle("nungambakkam 11:30 pm", channel="sms", user_id="u_sms")
    assert r["sms_text"].startswith("No bus now") and "Auto" in r["sms_text"]


def test_sms_start_and_reached_flow():
    orchestrator.handle("nungambakkam bus 8am", channel="sms", user_id="u_sms", user_phone="+15005550009")
    r = orchestrator.handle("START", channel="sms", user_id="u_sms", user_phone="+15005550009")
    assert r["sms_text"].startswith("Journey Watch ON")
    r = orchestrator.handle("REACHED", channel="sms", user_id="u_sms", user_phone="+15005550009")
    assert r["aval_state"] == "cheer" and "reached safely" in r["reply"]["text"]


def test_app_start_trip_asks_before_messaging():
    orchestrator.handle("Nungambakkam 8am")
    r = orchestrator.handle("start trip")
    assert r["card"]["type"] == "confirm" and r["actions"][0]["payload"]["confirmed"] is True


def test_safe_route_home_card():
    r = orchestrator.handle("safe way home 9:40 pm")
    assert r["card"]["type"] == "safe_route"
    assert r["card"]["paths"][0]["name"] == "Main road"
    assert any(a["id"] == "ask_to_meet" and a["needs_confirmation"] for a in r["actions"])


def test_places_and_place_details():
    r = orchestrator.handle("pharmacy open now near Nungambakkam")
    assert r["card"]["type"] == "places" and all(p["type"] == "pharmacy" for p in r["card"]["places"])
    r = orchestrator.handle("tell me about Lakshmi SHG kiosk")
    assert r["card"]["type"] == "place" and r["card"]["place"]["id"] == "p1"
    r = orchestrator.handle("Anna Nagar West to Nungambakkam 8am")
    assert r["intake"]["intent"] == "plan_trip"  # not the 'Anna Nagar West Police Booth' 


def test_free_bus_now():
    r = orchestrator.handle("free bus now", now=at("08:00"))
    assert r["card"]["type"] == "arrivals"


def test_unknown_gets_fallback():
    r = orchestrator.handle("blah blah")
    assert r["reply"]["text"] == "Sorry, send place name. Eg: Nungambakkam bus"
    assert r["sms_text"] == "Sorry, send place name. Eg: Nungambakkam bus"
