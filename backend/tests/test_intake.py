import json

import httpx

from backend.agents import intake


def test_rules_parse_english_trip_with_child():
    r = intake.parse("Nungambakkam, 8am, with my daughter")
    assert r["intent"] == "plan_trip"
    assert r["to"] == "Nungambakkam"
    assert r["time"] == "08:00"
    assert r["with_child"] is True
    assert r["lang"] == "en"
    assert r["source"] == "rules"


def test_rules_parse_tamil_voice_example():
    r = intake.parse("நுங்கம்பாக்கம், 8 மணி, பொண்ணோட")
    assert (r["intent"], r["to"], r["time"], r["with_child"], r["lang"]) == ("plan_trip", "Nungambakkam", "08:00", True, "ta")


def test_rules_parse_tanglish_from_to():
    r = intake.parse("Anna Nagar West to Nungambakkam 8 mani paapa kooda")
    assert (r["from"], r["to"], r["time"], r["with_child"], r["lang"]) == ("Anna Nagar West", "Nungambakkam", "08:00", True, "tanglish")


def test_rules_parse_reversed_from():
    r = intake.parse("to Nungambakkam from Kilpauk")
    assert (r["from"], r["to"]) == ("Kilpauk", "Nungambakkam")


def test_sms_commands():
    assert intake.parse("START")["intent"] == "start_trip"
    assert intake.parse("reached")["intent"] == "reached"
    assert intake.parse("HELP")["intent"] == "sos"
    assert intake.parse("help me stuck at teynampet")["intent"] == "sos"


def test_other_intents():
    assert intake.parse("safe way home")["intent"] == "safe_route_home"
    r = intake.parse("pharmacy open now")
    assert (r["intent"], r["place_type"]) == ("places_open_now", "pharmacy")
    assert intake.parse("free bus now")["intent"] == "free_bus_now"
    assert intake.parse("book ticket")["intent"] == "book_ticket"
    assert intake.parse("is Lakshmi SHG kiosk safe?")["intent"] == "place_details"
    assert intake.parse("what can you do")["intent"] == "help"


def test_night_time_parsing():
    assert intake.parse_time("9 mani iravu") == "21:00"
    assert intake.parse_time("9:40 pm") == "21:40"
    assert intake.parse_time("now") == "now"


def test_unknown_place_is_not_invented():
    r = intake.parse("Fake Nagar")
    assert r["to"] is None and r["intent"] == "unknown"


def test_gemini_valid_json_is_used():
    llm = lambda t: json.dumps({"intent": "plan_trip", "from": None, "to": "Nungambakkam", "time": "08:00",
                                "with_child": True, "lang": "ta", "confidence": 0.9})
    r = intake.parse("anything", llm=llm)
    assert r["source"] == "gemini" and r["to"] == "Nungambakkam" and r["with_child"] is True


def test_gemini_invalid_json_gives_fallback():
    r = intake.parse("Nungambakkam bus", llm=lambda t: "Sure! Here you go: {not json")
    assert r["intent"] == "unknown" and r["fallback"] is True and r["reason"] == "llm_invalid_json"


def test_gemini_wrong_schema_gives_fallback():
    bad = [{"intent": "book_flight"}, {"intent": "plan_trip", "with_child": "yes"}, ["plan_trip"], {"to": "x"}]
    for obj in bad:
        r = intake.parse("Nungambakkam bus", llm=lambda t, o=obj: json.dumps(o))
        assert r["fallback"] is True, obj


def test_gemini_network_error_uses_rules():
    def boom(t):
        raise httpx.ConnectError("down")
    r = intake.parse("Nungambakkam bus", llm=boom)
    assert r["source"] == "rules" and r["to"] == "Nungambakkam" and r["llm_error"] == "ConnectError"


def test_llm_never_sees_phone_or_name():
    seen = {}

    def spy(t):
        seen["text"] = t
        return json.dumps({"intent": "sos", "with_child": False})
    intake.parse("I am Priya, call +91 98765 43210 now", names=["Priya"], llm=spy)
    assert "98765" not in seen["text"] and "Priya" not in seen["text"]
    assert "[PHONE]" in seen["text"] and "[NAME]" in seen["text"]


def test_gemini_place_name_must_exist():
    llm = lambda t: json.dumps({"intent": "place_details", "place_name": "Imaginary Cafe", "with_child": False})
    assert intake.parse("x", llm=llm)["place_name"] is None
