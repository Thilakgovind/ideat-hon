import hashlib
import hmac

from backend import config
from backend.agents import pay, route
from backend.tests.conftest import FakeResponse


def metro_option():
    return next(o for o in route.plan("Anna Nagar West", "Nungambakkam", "08:00")["options"] if o["kind"] == "bus+metro")


def bus_option():
    return next(o for o in route.plan("Anna Nagar West", "Nungambakkam", "08:00")["options"] if o["kind"] == "bus")


def test_pay_needs_confirmation():
    r = pay.create_order(metro_option(), "Anna Nagar West", "Nungambakkam")
    assert r["needs_confirmation"] and r["summary"]["amount_inr"] == 30
    assert not pay.ORDERS


def test_free_trip_needs_no_payment():
    r = pay.create_order(bus_option(), "Anna Nagar West", "Nungambakkam", confirmed=True)
    assert r["free"] and r["ticket"]["amount_inr"] == 0


def test_auto_is_not_bookable():
    auto = next(o for o in route.plan("Anna Nagar West", "Nungambakkam", "08:00")["options"] if o["kind"] == "auto")
    assert pay.create_order(auto, "A", "B", confirmed=True)["error"] == "auto_not_bookable"


def test_mock_order_verify_ticket():
    o = pay.create_order(metro_option(), "Anna Nagar West", "Nungambakkam", confirmed=True)
    assert o["mode"] == "mock" and o["amount_paise"] == 3000 and "checkout_key_id" not in o
    assert pay.verify(o["order_id"], "pay_mock_1", "wrong")["error"] == "signature_invalid"
    t = pay.verify(o["order_id"], "pay_mock_1", "mock")["ticket"]
    assert t["qr_data"].startswith("SAFEPATH|TKT-") and t["women_coach"] and t["platform"]
    assert t["is_test"] is True
    assert pay.verify(o["order_id"], "pay_mock_1", "mock")["ticket"]["ticket_id"] == t["ticket_id"]  # idempotent


def test_live_key_is_refused(monkeypatch):
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_live_fake")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "s")
    called = []
    monkeypatch.setattr(pay.httpx, "post", lambda *a, **k: called.append(1))
    o = pay.create_order(metro_option(), "A", "B", confirmed=True)
    assert config.razorpay_mode() == "refused_live"
    assert o["mode"] == "mock" and o["fallback_reason"] == "live_key_refused" and not called


def test_test_mode_order_and_signature(monkeypatch):
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_fake")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "secret123")
    monkeypatch.setattr(pay.httpx, "post", lambda *a, **k: FakeResponse(200, {"id": "order_T1"}))
    o = pay.create_order(metro_option(), "A", "B", confirmed=True)
    assert o["mode"] == "test" and o["order_id"] == "order_T1"
    good = hmac.new(b"secret123", b"order_T1|pay_1", hashlib.sha256).hexdigest()
    assert pay.verify("order_T1", "pay_1", "mock")["error"] == "signature_invalid"
    assert pay.verify("order_T1", "pay_1", good)["ticket"]["payment_mode"] == "test"


def test_razorpay_error_falls_back_to_mock(monkeypatch):
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_fake")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "x")
    def boom(*a, **k):
        raise pay.httpx.ConnectError("down")
    monkeypatch.setattr(pay.httpx, "post", boom)
    o = pay.create_order(metro_option(), "A", "B", confirmed=True)
    assert o["mode"] == "mock" and o["fallback_reason"] == "razorpay_error"
