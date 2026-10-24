"""Voice agent: Sarvam AI speech-to-text and text-to-speech (Tamil).

Mock when SARVAM_API_KEY is missing or Sarvam fails: STT returns the provided
hint (or a demo sentence), TTS returns no audio so the app can fall back to
on-device speech.
"""
import httpx

from .. import config

STT_URL = "https://api.sarvam.ai/speech-to-text"
TTS_URL = "https://api.sarvam.ai/text-to-speech"
LANG_CODES = {"ta": "ta-IN", "en": "en-IN", "tanglish": "ta-IN"}
DEMO_TRANSCRIPT = "நுங்கம்பாக்கம், 8 மணி, பொண்ணோட"


def _headers():
    return {"api-subscription-key": config.env("SARVAM_API_KEY")}


def stt(audio: bytes, filename: str = "audio.wav", content_type: str = "audio/wav",
        lang: str = "ta", hint: str = None) -> dict:
    if config.has("sarvam") and audio:
        try:
            r = httpx.post(
                STT_URL, headers=_headers(),
                files={"file": (filename, audio, content_type)},
                data={"model": "saarika:v2.5", "language_code": LANG_CODES.get(lang, "unknown")},
                timeout=30,
            )
            if r.status_code == 200:
                body = r.json()
                return {"text": body.get("transcript", ""), "lang_code": body.get("language_code"), "provider": "sarvam"}
            err = f"sarvam_http_{r.status_code}"
        except httpx.HTTPError as e:
            err = type(e).__name__
        return {"text": hint or DEMO_TRANSCRIPT, "provider": "mock", "fallback_reason": err}
    return {"text": hint or DEMO_TRANSCRIPT, "provider": "mock",
            "fallback_reason": "no_key" if not config.has("sarvam") else "no_audio"}


def tts(text: str, lang: str = "ta") -> dict:
    if config.has("sarvam") and text:
        try:
            r = httpx.post(
                TTS_URL, headers=_headers(),
                json={"text": text[:500], "target_language_code": LANG_CODES.get(lang, "ta-IN"),
                      "speaker": "anushka", "model": "bulbul:v2"},
                timeout=30,
            )
            if r.status_code == 200:
                audios = r.json().get("audios") or []
                if audios:
                    return {"audio_base64": audios[0], "format": "wav", "provider": "sarvam"}
            err = f"sarvam_http_{r.status_code}"
        except httpx.HTTPError as e:
            err = type(e).__name__
        return {"audio_base64": None, "provider": "mock", "fallback_reason": err, "speak_text": text}
    return {"audio_base64": None, "provider": "mock", "fallback_reason": "no_key", "speak_text": text}
