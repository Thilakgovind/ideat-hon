import json

from backend import guardrails, orchestrator
from backend.agents import circle
from backend.tests.helpers import REAL_BUSES, sms_bus


# 1. strip phone numbers and names before the LLM
def test_redact_phone_email_name():
    out = guardrails.redact("I'm Priya, call 5000011111 or +91 50000-11111, mail p@x.com", names=["Priya"])
    assert "50000" not in out and "p@x.com" not in out and "Priya" not in out
    assert out.count("[PHONE]") == 2 and "[EMAIL]" in out


def test_redact_keeps_times_and_routes():
    assert guardrails.redact("21G at 8:30, 9 mani") == "21G at 8:30, 9 mani"


def test_personal_names_keep_relations():
    names = guardrails.personal_names(circle.STORE.user("u_demo"))
    assert "Priya" in names and "Kavya" in names and "Amma" not in names


def test_orchestrator_redacts_before_llm():
    seen = {}

    def spy(t):
        seen["t"] = t
        return json.dumps({"intent": "plan_trip", "to": "Nungambakkam", "with_child": False})
    orchestrator.handle("Kavya and I go to Nungambakkam, my number 5000011111", llm=spy)
    assert "Kavya" not in seen["t"] and "5000011111" not in seen["t"]


# 2. LLM never invents buses / places / fares
def test_llm_invented_place_gets_no_route():
    llm = lambda t: json.dumps({"intent": "plan_trip", "from": "Anna Nagar West", "to": "Atlantis Nagar", "with_child": False})
    r = orchestrator.handle("x", llm=llm)
    assert r["card"]["type"] == "no_route" and "Atlantis" in r["card"]["unmatched"][0]


def test_reply_facts_come_from_data_not_llm():
    llm = lambda t: json.dumps({"intent": "plan_trip", "to": "Nungambakkam", "time": "08:00", "with_child": False,
                                "bus": "99Z", "fare": 5})  # extra invented fields are ignored
    r = orchestrator.handle("x", llm=llm)
    assert "99Z" not in r["reply"]["text"] and r["card"]["option"]["legs"][1]["label"] in REAL_BUSES


def test_verify_options_drops_unknown_routes():
    fake = {"legs": [{"mode": "bus", "route_id": "99Z"}]}
    real = {"legs": [{"mode": "bus", "route_id": "MTC-18683"}, {"mode": "walk"}]}
    assert guardrails.verify_options([fake, real]) == [real]


# 3. confirm before paying or messaging; SOS skips
def test_confirmation_rules():
    assert guardrails.needs_confirmation("pay", False)
    assert guardrails.needs_confirmation("message", False)
    assert not guardrails.needs_confirmation("pay", True)
    assert not guardrails.needs_confirmation("sos", False)


def test_chat_book_ticket_only_asks():
    orchestrator.handle("Anna Nagar West to Nungambakkam 8am")
    r = orchestrator.handle("book ticket")
    assert r["card"]["type"] == "confirm" and r["card"]["action"] == "pay"
    from backend.agents import pay
    assert not pay.ORDERS  # nothing charged or created


def test_chat_sos_acts_immediately():
    r = orchestrator.handle("help me, someone is following me")
    assert r["card"]["type"] == "sos" and r["aval_state"] == "alert"
    assert r["card"]["confirmation_skipped"]


# 4. location only during trip or SOS
def test_location_rules():
    assert not guardrails.location_allowed()
    assert guardrails.location_allowed(trip_active=True)
    assert guardrails.location_allowed(sos_active=True)
    assert guardrails.filter_location({"lat": 1, "lng": 2, "x": 3}, False) == {"x": 3}


# 5. anonymous logs
def test_anonymous_log_whitelist():
    entry = guardrails.anonymous_log({"intent": "plan_trip", "to_area": "Nungambakkam", "from_area": "my house 5th street",
                                      "phone": "+915000011111", "name": "Priya", "text": "secret", "hour": 8})
    assert entry == {"intent": "plan_trip", "to_area": "Nungambakkam", "from_area": "other", "hour": 8}


def test_chat_log_has_no_text_or_phone():
    guardrails.REQUEST_LOG.clear()
    orchestrator.handle("Priya here, 5000011111, Nungambakkam bus", channel="sms", user_phone="+915000011111")
    dumped = json.dumps(list(guardrails.REQUEST_LOG))
    assert "50000" not in dumped and "Priya" not in dumped


# 6. never claim an alert was sent unless it was
def test_demo_sos_reply_is_honest():
    r = orchestrator.handle("SOS")
    assert "not sent" in r["reply"]["text"].lower()
    assert "is informed" not in r["reply"]["text"]


def test_describe_delivery():
    d = guardrails.describe_delivery([{"status": "sent"}, {"status": "mock_logged"}, {"status": "failed"}])
    assert d == {"sent": 1, "demo_logged": 1, "not_sent": 1, "any_real_alert": True}


def test_sms_clamp():
    assert len(guardrails.clamp_sms("a" * 200)) == 160
    assert len(guardrails.clamp_sms("அ" * 100, tamil=True)) == 70
