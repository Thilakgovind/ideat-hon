"""Voice call-back: she texts CALL -> Twilio calls her -> AVAL speaks Tamil (Sarvam TTS)
-> <Record> her question -> Sarvam STT -> orchestrator -> spoken answer.

Needs Twilio keys + PUBLIC_BACKEND_URL (ngrok). Trial Twilio accounts can only call
verified numbers. Any failure falls back to SMS. Nothing here logs phone numbers.
"""
import threading
import time
import uuid
import xml.sax.saxutils as sax
from collections import OrderedDict

import httpx

from .. import config
from . import sms, voice

CALLS_URL = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Calls.json"
GREETING = {"ta": "வணக்கம், நான் அவள். எங்கே போக வேண்டும்? பீப் ஒலிக்குப் பிறகு சொல்லுங்கள்.",
            "en": "Hello, this is AVAL. Where do you want to go? Tell me after the beep."}
AUDIO: "OrderedDict[str, bytes]" = OrderedDict()   # short-lived TTS clips served to Twilio
JOBS: dict = {}                                       # job id -> {"status", "twiml", "created"}
MAX_AUDIO = 50
MAX_POLLS = 6


def ready() -> tuple:
    if not config.has("twilio"):
        return False, "twilio_keys_missing"
    if not config.env("PUBLIC_BACKEND_URL").startswith("https://"):
        return False, "public_backend_url_missing"
    return True, ""


def _url(path: str) -> str:
    return config.env("PUBLIC_BACKEND_URL").rstrip("/") + path


def start(phone: str, lang: str = "ta") -> dict:
    """Place the outbound call. Returns status calling | not_started (+reason)."""
    ok, reason = ready()
    if not ok:
        return {"status": "not_started", "reason": reason}
    if not phone or sms.FAKE_NUMBER.match(phone.replace(" ", "")):
        return {"status": "not_started", "reason": "no_real_number"}
    try:
        r = httpx.post(CALLS_URL.format(sid=config.env("TWILIO_ACCOUNT_SID")),
                       data={"To": phone, "From": config.env("TWILIO_PHONE_NUMBER"),
                             "Url": _url(f"/api/voice/call/start?lang={lang}"), "Method": "POST"},
                       auth=(config.env("TWILIO_ACCOUNT_SID"), config.env("TWILIO_AUTH_TOKEN")), timeout=15)
    except httpx.HTTPError as e:
        return {"status": "not_started", "reason": type(e).__name__}
    if r.status_code in (200, 201):
        return {"status": "calling", "ref": r.json().get("sid")}
    return {"status": "not_started", "reason": f"twilio_http_{r.status_code}"}


def _store_audio(b64: str) -> str:
    import base64
    clip_id = uuid.uuid4().hex[:16]
    AUDIO[clip_id] = base64.b64decode(b64)
    while len(AUDIO) > MAX_AUDIO:
        AUDIO.popitem(last=False)
    return clip_id


def _speak(text: str, lang: str) -> str:
    """<Play> Sarvam audio when available, else Twilio <Say> as a fallback."""
    spoken = voice.tts(text, lang)
    if spoken.get("audio_base64"):
        clip = _store_audio(spoken["audio_base64"])
        return f"<Play>{sax.escape(_url(f'/api/voice/audio/{clip}.wav'))}</Play>"
    return f'<Say language="{"ta-IN" if lang == "ta" else "en-IN"}">{sax.escape(text)}</Say>'


def _record(lang: str) -> str:
    action = sax.escape(_url(f"/api/voice/call/recorded?lang={lang}"))
    return f'<Record action="{action}" method="POST" maxLength="15" timeout="3" playBeep="true" trim="trim-silence"/>'


def twiml(body: str) -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?><Response>{body}</Response>'


def twiml_start(lang: str = "ta") -> str:
    return twiml(_speak(GREETING.get(lang, GREETING["en"]), lang) + _record(lang))


def _process(job_id: str, recording_url: str, caller: str, lang: str):
    """Background: download recording -> STT -> AVAL -> TTS. Falls back to SMS on any failure."""
    from .. import orchestrator
    from .circle import user_id_for_phone
    reply_sms = None
    try:
        audio = httpx.get(recording_url + ".wav", auth=(config.env("TWILIO_ACCOUNT_SID"), config.env("TWILIO_AUTH_TOKEN")),
                          timeout=20, follow_redirects=True)
        heard = voice.stt(audio.content if audio.status_code == 200 else b"", "speech.wav", "audio/wav", lang=lang)
        if heard["provider"] != "sarvam" or not heard["text"]:
            raise RuntimeError("stt_failed")
        result = orchestrator.handle(heard["text"], lang=lang, channel="call", user_id=user_id_for_phone(caller), user_phone=caller)
        reply_sms = result["sms_text"]
        JOBS[job_id].update(status="done", twiml=twiml(_speak(result["reply"]["text"], result["reply"]["lang"]) +
                                                       '<Pause length="1"/>' + _record(lang)))
    except Exception:  # noqa: BLE001 - never leave the caller hanging
        fallback = "Sorry, I could not hear that. I have sent you an SMS." if lang != "ta" else "மன்னிக்கவும், கேட்கவில்லை. SMS அனுப்பியுள்ளேன்."
        JOBS[job_id].update(status="failed", twiml=twiml(_speak(fallback, lang) + "<Hangup/>"))
        sms.send(caller, reply_sms or "SafePath: send your trip by SMS. Eg: Nungambakkam bus", purpose="call_fallback")


def twiml_recorded(recording_url: str, caller: str, lang: str = "ta") -> str:
    if not recording_url:
        return twiml(_speak(GREETING.get(lang, GREETING["en"]), lang) + _record(lang))
    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {"status": "working", "twiml": None, "created": time.time(), "polls": 0}
    threading.Thread(target=_process, args=(job_id, recording_url, caller, lang), daemon=True).start()
    return twiml(f'<Pause length="4"/><Redirect method="POST">{sax.escape(_url(f"/api/voice/call/answer?job={job_id}&lang={lang}"))}</Redirect>')


def twiml_answer(job_id: str, lang: str = "ta") -> str:
    job = JOBS.get(job_id)
    if not job:
        return twiml("<Hangup/>")
    if job["twiml"]:
        JOBS.pop(job_id, None)
        return job["twiml"]
    job["polls"] += 1
    if job["polls"] > MAX_POLLS:
        JOBS.pop(job_id, None)
        return twiml(_speak("I have sent you an SMS. Goodbye." if lang != "ta" else "SMS அனுப்பியுள்ளேன். நன்றி.", lang) + "<Hangup/>")
    return twiml(f'<Pause length="3"/><Redirect method="POST">{sax.escape(_url(f"/api/voice/call/answer?job={job_id}&lang={lang}"))}</Redirect>')
