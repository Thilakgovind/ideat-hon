"""V1.1 live-service wiring: SMS provider switch, textbee inbound, call-back, storage, n8n demo route."""
import base64
import hashlib
import hmac
import json

import httpx
from fastapi.testclient import TestClient

from backend import config, data, store
from backend.agents import callback, sms
from backend.app import app
from backend.tests.conftest import FakeResponse

c = TestClient(app)
REAL = "+919876500001"  # never dialled: every provider call is faked below


def textbee_env(monkeypatch):
    monkeypatch.setenv("SMS_PROVIDER", "textbee")
    monkeypatch.setenv("TEXTBEE_API_KEY", "k")
    monkeypatch.setenv("TEXTBEE_DEVICE_ID", "dev1")


# ---------------------------------------------------------------- provider switch

def test_provider_selection(monkeypatch):
    assert config.sms_provider() == "mock"
    textbee_env(monkeypatch)
    assert config.sms_provider() == "textbee"
    monkeypatch.setenv("SMS_PROVIDER", "fast2sms")  # selected but no key -> mock, never crash
    assert config.sms_provider() == "mock"
    monkeypatch.setenv("SMS_PROVIDER", "nonsense")
    assert config.sms_provider() == "mock"


def test_textbee_send_and_failure_fallback(monkeypatch):
    textbee_env(monkeypatch)
    calls = []

    def ok(url, **kw):
        calls.append((url, kw))
        return FakeResponse(201, {"data": {"smsBatchId": "b1"}})
    monkeypatch.setattr(sms.httpx, "post", ok)
    r = sms.send(REAL, "hello")
    assert r["status"] == "sent" and r["provider"] == "textbee" and r["ref"] == "b1"
    assert "dev1" in calls[0][0] and calls[0][1]["json"]["recipients"] == [REAL]

    def boom(*a, **k):
        raise httpx.ConnectError("down")
    monkeypatch.setattr(sms.httpx, "post", boom)
    r = sms.send(REAL, "hello")
    assert r["status"] == "not_sent" and r["reason"] == "ConnectError"
    assert list(sms.OUTBOX)[-1]["status"] == "not_sent"  # still logged for the demo outbox
    assert "9876500001" not in json.dumps(list(sms.OUTBOX))


def test_sample_numbers_are_never_sent(monkeypatch):
    textbee_env(monkeypatch)
    monkeypatch.setattr(sms.httpx, "post", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not call provider")))
    r = sms.send("+910000000011", "alert")
    assert (r["status"], r["reason"]) == ("not_sent", "sample_number")


def test_fast2sms_outbound(monkeypatch):
    monkeypatch.setenv("SMS_PROVIDER", "fast2sms")
    monkeypatch.setenv("FAST2SMS_API_KEY", "k")
    seen = {}

    def fake(url, **kw):
        seen.update(kw["json"])
        return FakeResponse(200, {"return": True, "request_id": "r1"})
    monkeypatch.setattr(sms.httpx, "post", fake)
    assert sms.send(REAL, "hi")["status"] == "sent" and seen["numbers"] == "9876500001"


def test_tamil_sms_limit(monkeypatch):
    assert len(sms.send(REAL, "அ" * 200)["body"]) == 70


# ---------------------------------------------------------------- textbee inbound

def test_textbee_inbound_replies_via_provider(monkeypatch):
    textbee_env(monkeypatch)
    sent = []
    monkeypatch.setattr(sms.httpx, "post", lambda url, **kw: sent.append(kw["json"]) or FakeResponse(201, {"data": {}}))
    payload = {"event": "MESSAGE_RECEIVED", "data": {"sender": REAL, "message": "nungambakkam bus 8am", "receivedAt": "t1"}}
    r = c.post("/api/sms/textbee", json=payload).json()
    assert r["ok"] and r["intent"] == "plan_trip" and r["reply_status"] == "sent"
    assert "21G" in sent[0]["message"] and len(sent[0]["message"]) <= 160
    assert c.post("/api/sms/textbee", json=payload).json()["ignored"] == "duplicate"


def test_textbee_ignores_junk():
    for junk in ([], {"event": "MESSAGE_SENT", "data": {"sender": REAL, "message": "x"}}, {"data": {"sender": "abc", "message": "x"}},
                 {"data": {"sender": REAL}}, {"hello": "world"}):
        r = c.post("/api/sms/textbee", json=junk)
        assert r.status_code == 200 and "ignored" in r.json()
    assert c.post("/api/sms/textbee", content=b"not json", headers={"content-type": "application/json"}).json()["ignored"]


def test_textbee_signature_when_secret_set(monkeypatch):
    monkeypatch.setenv("TEXTBEE_WEBHOOK_SECRET", "s3")
    raw = json.dumps({"event": "MESSAGE_RECEIVED", "data": {"sender": REAL, "message": "help"}}).encode()
    assert c.post("/api/sms/textbee", content=raw, headers={"content-type": "application/json", "x-signature": "bad"}).status_code == 403
    good = hmac.new(b"s3", raw, hashlib.sha256).hexdigest()
    assert c.post("/api/sms/textbee", content=raw, headers={"content-type": "application/json", "x-signature": good}).status_code == 200


def test_commands_over_textbee(monkeypatch):
    textbee_env(monkeypatch)
    monkeypatch.setattr(sms.httpx, "post", lambda url, **kw: FakeResponse(201, {"data": {}}))
    for i, (text, intent) in enumerate([("nungambakkam bus 8am", "plan_trip"), ("START", "start_trip"),
                                        ("REACHED", "reached"), ("HELP", "sos"), ("CALL", "call_me")]):
        body = {"event": "MESSAGE_RECEIVED", "data": {"sender": "+919876500002", "message": text, "receivedAt": str(i)}}
        assert c.post("/api/sms/textbee", json=body).json()["intent"] == intent


# ---------------------------------------------------------------- call-back

def test_call_back_falls_back_without_public_url(monkeypatch):
    for k, v in {"TWILIO_ACCOUNT_SID": "ACx", "TWILIO_AUTH_TOKEN": "t", "TWILIO_PHONE_NUMBER": "+15005550006"}.items():
        monkeypatch.setenv(k, v)
    assert callback.ready() == (False, "public_backend_url_missing")
    from backend import orchestrator
    r = orchestrator.handle("CALL", channel="sms", user_id="u_x", user_phone=REAL)
    assert r["card"]["status"] == "not_started" and "not available" in r["reply"]["text"]


def test_call_back_places_call_and_serves_twiml(monkeypatch):
    for k, v in {"TWILIO_ACCOUNT_SID": "ACx", "TWILIO_AUTH_TOKEN": "t", "TWILIO_PHONE_NUMBER": "+15005550006",
                 "PUBLIC_BACKEND_URL": "https://demo.ngrok.app", "SARVAM_API_KEY": "k"}.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setattr(callback.httpx, "post", lambda *a, **k: FakeResponse(201, {"sid": "CA1"}))
    assert callback.start(REAL)["status"] == "calling"
    assert callback.start("+910000000011")["status"] == "not_started"  # sample numbers are never called
    audio = base64.b64encode(b"RIFFfake").decode()
    from backend.agents import voice
    monkeypatch.setattr(voice.httpx, "post", lambda *a, **k: FakeResponse(200, {"audios": [audio]}))
    xml = callback.twiml_start("ta")
    assert "<Play>https://demo.ngrok.app/api/voice/audio/" in xml and "<Record" in xml
    clip = xml.split("/api/voice/audio/")[1].split(".wav")[0]
    monkeypatch.setenv("PUBLIC_BACKEND_URL", "")  # skip Twilio signature for the local GET
    assert c.get(f"/api/voice/audio/{clip}.wav").content == b"RIFFfake"


def test_call_answer_polls_then_hangs_up(monkeypatch):
    monkeypatch.setenv("PUBLIC_BACKEND_URL", "https://demo.ngrok.app")
    callback.JOBS["j1"] = {"status": "working", "twiml": None, "created": 0, "polls": 0}
    assert "<Redirect" in callback.twiml_answer("j1", "en")
    callback.JOBS["j1"]["polls"] = callback.MAX_POLLS
    assert "<Hangup/>" in callback.twiml_answer("j1", "en")


def test_twilio_webhook_signature(monkeypatch):
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "tok")
    monkeypatch.setenv("PUBLIC_BACKEND_URL", "https://demo.ngrok.app")
    form = {"From": REAL, "Body": "START"}
    assert c.post("/api/sms/webhook", data=form, headers={"X-Twilio-Signature": "bad"}).status_code == 403
    url = "https://demo.ngrok.app/api/sms/webhook"
    sig = base64.b64encode(hmac.new(b"tok", (url + "".join(k + form[k] for k in sorted(form))).encode(), hashlib.sha1).digest()).decode()
    assert c.post("/api/sms/webhook", data=form, headers={"X-Twilio-Signature": sig}).status_code == 200


def test_voice_reply_is_short():
    from backend.agents import voice
    long = "Here is your safest way. " * 30
    assert len(voice.short_for_voice(long)) <= voice.MAX_TTS_CHARS


# ---------------------------------------------------------------- storage

def test_memory_mode_without_supabase():
    assert store.available() is False and store.status()["mode"] == "memory"
    assert store.load_public() == {} and data.SOURCE.get("places", "json") == "json"
    assert store.persist("trips", {"id": "x"}) is None  # no-op in memory mode


def test_supabase_mode_loads_public_tables(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "k")
    tables = {
        "places": [{"id": "s1", "name": "Test Kiosk", "type": "shg_kiosk", "area": "Adyar", "near_stop": "S1", "lat": 13.0,
                    "lng": 80.25, "open_time": "06:00:00", "close_time": "22:00:00", "crowd_by_hour": {"08": "busy"},
                    "women_run": True, "source": "sample"}],
        "reviews": [{"place_id": "s1", "author": "Meena (sample)", "rating": 5, "lang": "en", "body": "Safe", "days_ago": 1}],
        "stops": [{"id": "S1", "name": "Stop One", "area": "Adyar", "lat": 13.0, "lng": 80.25},
                  {"id": "S2", "name": "Stop Two", "area": "Guindy", "lat": 13.01, "lng": 80.22}],
        "routes": [{"id": "99", "number": "99", "mode": "bus", "name": "One - Two", "free_for_women": True, "fare_inr": 0,
                    "stop_sequence": [{"stop_id": "S1", "min": 0}, {"stop_id": "S2", "min": 10}],
                    "first_departure": "05:00:00", "last_departure": "22:00:00", "frequency_min": 10}],
        "transfers": [],
    }

    def fake_get(url, **kw):
        if kw.get("params", {}).get("limit") == 1:
            return FakeResponse(200, [{"id": "s1"}])
        return FakeResponse(200, tables[url.rsplit("/", 1)[-1]])
    monkeypatch.setattr(store.httpx, "get", fake_get)
    loaded = store.load_public()
    assert loaded["places"] == 1 and store.status()["mode"] == "supabase"
    assert data.places()[0]["open"] == "06:00" and data.places()[0]["reviews"][0]["text"] == "Safe"
    assert data.routes()[0]["stops"][1]["name"] == "Stop Two" and data.SOURCE["places"] == "supabase"
    writes = []
    monkeypatch.setattr(store.httpx, "post", lambda url, **kw: writes.append(url) or FakeResponse(201))
    assert store.persist("trips", {"id": "t1"}, sync=True) is True and writes[0].endswith("/trips")


def test_supabase_unreachable_stays_memory(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "k")
    monkeypatch.setattr(store.httpx, "get", lambda *a, **k: FakeResponse(404, {"code": "PGRST205"}))
    assert store.available(force=True) is False and "run migrations" in store.status()["reason"]


# ---------------------------------------------------------------- n8n demo route

def test_demo_chat_direct_and_n8n_fallback(monkeypatch):
    r = c.post("/api/demo/chat", json={"text": "nungambakkam bus 8am"}).json()
    assert r["via"] == "backend" and "21G" in r["sms_text"] and r["agent_steps"]
    monkeypatch.setenv("N8N_ORCHESTRATOR_URL", "https://n8n.invalid/webhook/safepath-aval")

    class Down:
        def __init__(self, *a, **k): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def post(self, *a, **k): raise httpx.ConnectError("down")
    monkeypatch.setattr(httpx, "AsyncClient", Down)
    r = c.post("/api/demo/chat", json={"text": "nungambakkam bus 8am"}).json()
    assert r["via"].startswith("backend (n8n") and "21G" in r["sms_text"]


def test_health_reports_storage_and_call_back():
    h = c.get("/health").json()
    assert h["storage"]["mode"] == "memory" and h["call_back"].startswith("off") and h["version"] == "1.1.0"
