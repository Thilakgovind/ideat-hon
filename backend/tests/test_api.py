import io

from fastapi.testclient import TestClient

from backend.app import app

c = TestClient(app)
TRIP = {"from": "Anna Nagar West", "to": "Nungambakkam", "time": "08:00"}


def test_health_reports_services_without_values():
    r = c.get("/health").json()
    assert r["status"] == "ok" and r["services"]["gemini"] == "mock" and r["services"]["razorpay"] == "mock"


def test_chat_and_voice():
    r = c.post("/api/aval/chat", json={"text": "Nungambakkam 8am", "lang": "en"}).json()
    assert r["card"]["type"] == "route" and r["steps"]
    v = c.post("/api/aval/voice", data={"lang": "ta"}, files={"audio": ("a.wav", io.BytesIO(b"RIFF"), "audio/wav")}).json()
    assert v["stt_provider"] == "mock" and v["transcript"] and v["reply"]["lang"] == "ta"


def test_routes_sorting_and_arrivals():
    r = c.get("/api/routes", params={**TRIP, "sort": "cheapest"}).json()
    assert r["options"][0]["fare_inr"] == 0 and r["sort"] == "cheapest"
    assert c.get("/api/routes", params={"from": "Anna Nagar West", "time": "08:00"}).json()["arrivals"]
    assert c.get("/api/routes").status_code == 400
    assert c.get("/api/routes", params={"from": "Fake", "to": "Nungambakkam"}).json()["error"] == "no_match"


def test_safe_route():
    r = c.get("/api/safe-route", params={**TRIP, "time": "21:40"}).json()
    assert r["walk"]["paths"][0]["badge"] == "SAFEST" and "transit" in r


def test_places_endpoints():
    assert c.get("/api/places", params={"open_now": True, "time": "21:00"}).json()["count"] > 0
    assert c.get("/api/places/p1").json()["reviews"]
    assert c.get("/api/places/nope").status_code == 404


def test_trip_flow():
    body = {**TRIP, "option_id": "bus:21G:ANW"}
    assert c.post("/api/trip/start", json=body).json()["needs_confirmation"]
    trip = c.post("/api/trip/start", json={**body, "confirmed": True}).json()["trip"]
    assert c.get(f"/api/trip/{trip['trip_id']}").json()["trip"]["status"] == "active"
    assert c.post("/api/trip/checkin", json={"trip_id": trip["trip_id"]}).status_code == 200
    assert c.post("/api/trip/reached", json={"trip_id": trip["trip_id"]}).json()["trip"]["status"] == "reached"
    assert c.post("/api/trip/start", json={**body, "option_id": "bus:FAKE:X"}).status_code == 404
    assert c.post("/api/trip/reached", json={"trip_id": "nope"}).status_code == 404


def test_sos_endpoint():
    r = c.post("/api/sos", json={"lat": 13.06, "lng": 80.24}).json()
    assert r["sos"]["active"] and r["helplines"]
    assert c.post("/api/sos", json={"action": "stop"}).json()["sos"]["active"] is False


def test_circle_endpoints():
    assert len(c.get("/api/circle").json()["contacts"]) == 4
    assert c.post("/api/circle", json={"action": "add", "label": "Meera"}).json()["needs_confirmation"]
    added = c.post("/api/circle", json={"action": "add", "label": "Meera", "phone": "+919000000001", "confirmed": True}).json()
    assert "phone" not in added["contact"]
    assert c.post("/api/circle", json={"action": "bogus"}).status_code == 400


def test_pay_flow_amount_from_server():
    body = {**TRIP, "option_id": "bus+metro:70:M-PURPLE:ANW"}
    assert c.post("/api/pay/order", json=body).json()["needs_confirmation"]
    o = c.post("/api/pay/order", json={**body, "confirmed": True, "amount": 1}).json()  # client amount ignored
    assert o["amount_paise"] == 3000
    t = c.post("/api/pay/verify", json={"order_id": o["order_id"], "payment_id": "pay_mock_1", "signature": "mock"}).json()
    assert t["ticket"]["qr_data"].startswith("SAFEPATH|")
    assert c.post("/api/pay/verify", json={"order_id": o["order_id"], "payment_id": "x", "signature": "bad"}).status_code in (200, 400)
    assert c.post("/api/pay/verify", json={"order_id": "nope", "payment_id": "x", "signature": "y"}).status_code == 404


def test_sms_webhook_twiml():
    r = c.post("/api/sms/webhook", data={"From": "+15550002222", "Body": "nungambakkam bus 8am"})
    assert r.headers["content-type"].startswith("application/xml")
    assert "<Message>" in r.text and "21G" in r.text
    r = c.post("/api/sms/webhook", data={"From": "+15550002222", "Body": "START"})
    assert "Journey Watch ON" in r.text
    assert "2222" not in c.get("/api/demo/outbox").text
