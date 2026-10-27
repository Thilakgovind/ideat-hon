from backend.agents import sms, voice
from backend.tests.conftest import FakeResponse


# ---------- voice ----------

def test_stt_mock_without_key():
    r = voice.stt(b"RIFF....", hint="Nungambakkam bus")
    assert r == {"text": "Nungambakkam bus", "provider": "mock", "fallback_reason": "no_key"}
    assert voice.stt(b"")["text"] == voice.DEMO_TRANSCRIPT


def test_tts_mock_without_key():
    r = voice.tts("வணக்கம்")
    assert r["audio_base64"] is None and r["provider"] == "mock" and r["speak_text"] == "வணக்கம்"


def test_sarvam_real_call_shape(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "k")
    calls = []

    def fake(url, **kw):
        calls.append((url, kw))
        if url == voice.STT_URL:
            return FakeResponse(200, {"transcript": "நுங்கம்பாக்கம்", "language_code": "ta-IN"})
        return FakeResponse(200, {"audios": ["UklGRg=="]})
    monkeypatch.setattr(voice.httpx, "post", fake)
    assert voice.stt(b"abc")["provider"] == "sarvam"
    assert voice.tts("hi", "ta")["audio_base64"] == "UklGRg=="
    assert calls[0][1]["headers"]["api-subscription-key"] == "k"
    assert calls[1][1]["json"]["target_language_code"] == "ta-IN"


def test_sarvam_failure_falls_back(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "k")
    monkeypatch.setattr(voice.httpx, "post", lambda *a, **k: FakeResponse(500))
    assert voice.stt(b"abc", hint="x")["provider"] == "mock"
    assert voice.tts("x")["provider"] == "mock"


# ---------- sms ----------

def test_sms_mock_logs_and_masks():
    r = sms.send("+915000011111", "hello")
    assert r["status"] == "mock_logged" and r["to"] == "•••• 11"
    assert "50000" not in str(list(sms.OUTBOX))


def test_sms_clamped_to_160():
    assert len(sms.send("+911", "x" * 400)["body"]) == 160


def test_twilio_real_send(monkeypatch):
    for k, v in {"TWILIO_ACCOUNT_SID": "ACtest", "TWILIO_AUTH_TOKEN": "t", "TWILIO_PHONE_NUMBER": "+1555", "SMS_PROVIDER": "twilio"}.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setattr(sms.httpx, "post", lambda *a, **k: FakeResponse(201, {"sid": "SM1"}))
    assert sms.send("+15005550009", "hi")["status"] == "sent"
    r = sms.send(None, "hi")
    assert (r["status"], r["reason"]) == ("not_sent", "no_phone")
    monkeypatch.setattr(sms.httpx, "post", lambda *a, **k: FakeResponse(401))
    r = sms.send("+15005550009", "hi")
    assert (r["status"], r["reason"]) == ("not_sent", "twilio_http_401")


def test_inbound_and_twiml():
    assert sms.parse_inbound({"From": " +1555 ", "Body": " START "}) == {"from": "+1555", "body": "START"}
    assert "<Message>a &amp; b</Message>" in sms.twiml("a & b")
