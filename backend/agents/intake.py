"""Intake agent: free text (Tamil / English / Tanglish) -> validated JSON.

{intent, from, to, time, with_child, lang, place_type, place_name, confidence}

- Gemini parses when GEMINI_API_KEY is set. Its JSON is validated; invalid
  JSON -> intent "unknown" with fallback=True (the orchestrator sends the
  fallback reply). Gemini errors/timeouts -> rule-based parser.
- No key -> rule-based parser (demo mode).
- Text is redacted (phones, emails, names) before any LLM call.
"""
import json
import re

import httpx

from .. import config
from ..guardrails import redact
from . import route as route_agent

INTENTS = {"plan_trip", "safe_route_home", "places_open_now", "place_details", "free_bus_now", "book_ticket",
           "share_trip", "start_trip", "reached", "check_in", "stop", "sos", "help", "unknown"}
LANGS = {"ta", "en", "tanglish"}
PLACE_TYPES = {"pharmacy", "grocery", "tea_shop", "atm", "hospital", "police_booth", "shg_kiosk", "petrol_bunk",
               "bus_shelter", "bakery"}
FALLBACK_REPLY = "Sorry, tell me the place name. Eg: Nungambakkam bus"
FALLBACK_REPLY_TA = "மன்னிக்கவும், இடத்தின் பெயரைச் சொல்லுங்கள். உதா: நுங்கம்பாக்கம் பஸ்"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Adapted from agents/intake_agent_prompt.md for the V1 intents and schema.
SYSTEM_PROMPT = """You are the Intake Agent of SafePath (AVAL), a travel helper for women in Chennai.
Read one short message (Tamil, English or Tanglish) and return ONLY a JSON object:
{"intent": one of [plan_trip, safe_route_home, places_open_now, place_details, free_bus_now, book_ticket,
  share_trip, start_trip, reached, check_in, stop, sos, help, unknown],
 "from": place name or null, "to": place name or null,
 "time": "HH:MM" (24h) or "now" or null,
 "with_child": true/false, "lang": "ta" | "en" | "tanglish",
 "place_type": one of [pharmacy, grocery, tea_shop, atm, hospital, police_booth, shg_kiosk, petrol_bunk,
  bus_shelter, bakery] or null,
 "place_name": name of a specific shop/place asked about, or null,
 "confidence": 0..1}
Rules: "8 mani" = 08:00. "paapa"/"ponnu"/daughter/son = with_child true. HELP / danger / scared = sos.
START = start_trip. REACHED = reached. Copy place names as written; do not invent places, buses or fares.
Text in [PHONE]/[NAME] brackets was removed for privacy; ignore it. No markdown, no extra text."""

TANGLISH = {"mani", "paapa", "ponnu", "ponnoda", "kooda", "poganum", "poren", "enga", "veetuku", "veettuku",
            "iravu", "ippo", "akka", "amma", "kadai", "vanthuten", "vandhuten", "bayama", "saayangalam", "kaalai"}

KEYWORDS = [
    ("sos", ["sos", "help me", "danger", "unsafe", "scared", "following me", "save me", "bayama", "காப்பாற்று",
             "காப்பாத்து", "உதவி", "பயமா", "ஆபத்து"]),
    ("reached", ["reached", "i'm home", "im home", "i am home", "vanthuten", "vandhuten", "வந்துட்டேன்", "வந்தடைந்தேன்"]),
    ("start_trip", ["start trip", "start my trip", "boarded", "start journey", "பயணம் தொடங்கு"]),
    ("stop", ["stop watch", "stop tracking", "cancel trip"]),
    ("check_in", ["i am ok", "i'm ok", "im ok", "i am fine", "nalla irukken", "நலம்"]),
    ("share_trip", ["share my trip", "share trip", "send to amma", "tell amma", "share with", "பகிர்"]),
    ("help", ["what can you do", "how to use", "help menu", "என்ன செய்ய முடியும்"]),
    ("safe_route_home", ["safe way home", "safe route home", "walk home", "way home", "veetuku", "veettuku",
                         "வீட்டுக்கு", "வீட்டிற்கு"]),
    ("book_ticket", ["book", "ticket", "டிக்கெட்", "pay for"]),
    ("free_bus_now", ["free bus", "ilavasa", "இலவச"]),
    ("places_open_now", ["open now", "open at night", "is open", "shop open", "near me", "nearby", "kadai", "கடை", "திறந்து"]),
]
TYPE_WORDS = {
    "pharmacy": ["pharmacy", "medical", "medicine", "மருந்து"], "atm": ["atm"], "tea_shop": ["tea", "டீ", "chai"],
    "police_booth": ["police", "காவல்"], "hospital": ["hospital", "மருத்துவமனை"], "petrol_bunk": ["petrol"],
    "bakery": ["bakery", "பேக்கரி"], "grocery": ["grocery", "மளிகை"], "shg_kiosk": ["shg", "kiosk"],
}
CHILD_WORDS = ["child", "daughter", "son", "kid", "kids", "baby", "paapa", "ponnu", "ponnoda", "pullai", "kuzhandhai",
               "மகள்", "மகன்", "குழந்தை", "பாப்பா", "பொண்ணோட", "பொண்ணு", "பிள்ளை"]
COMMANDS = {"start": "start_trip", "reached": "reached", "help": "sos", "sos": "sos", "stop": "stop",
            "check": "check_in", "ok": "check_in"}


def detect_lang(text: str) -> str:
    if any("஀" <= ch <= "௿" for ch in text):
        return "ta"
    words = set(re.findall(r"[a-z]+", text.lower()))
    return "tanglish" if words & TANGLISH else "en"


def parse_time(text: str):
    t = text.lower()
    night = any(w in t for w in ("night", "iravu", "இரவு", "pm", "evening", "மாலை", "saayangalam"))
    m = re.search(r"\b(\d{1,2})[:.](\d{2})\s*(am|pm)?", t)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        if m.group(3) == "pm" and h < 12:
            h += 12
        if m.group(3) == "am" and h == 12:
            h = 0
        return f"{h:02d}:{mi:02d}" if h < 24 and mi < 60 else None
    m = re.search(r"\b(\d{1,2})\s*(am|pm|mani|மணி|o'?clock)", t)
    if m:
        h = int(m.group(1))
        if h > 23:
            return None
        if m.group(2) == "pm" and h < 12:
            h += 12
        elif m.group(2) == "am" and h == 12:
            h = 0
        elif m.group(2) not in ("am", "pm") and night and h < 12:
            h += 12
        return f"{h:02d}:00"
    if any(w in t for w in ("now", "ippo", "இப்போ", "இப்பொழுது")):
        return "now"
    if any(w in t for w in ("morning", "kaalai", "காலை")):
        return "08:00"
    if any(w in t for w in ("evening", "saayangalam", "மாலை")):
        return "18:00"
    if any(w in t for w in ("night", "iravu", "இரவு")):
        return "21:00"
    return None


def _has(t, words):
    return any(re.search(rf"(?<![a-z]){re.escape(w)}(?![a-z])", t) if w.isascii() else w in t for w in words)


def rule_parse(text: str) -> dict:
    t = text.lower().strip()
    lang = detect_lang(text)
    out = {"intent": "unknown", "from": None, "to": None, "time": parse_time(text), "with_child": _has(t, CHILD_WORDS),
           "lang": lang, "place_type": None, "place_name": None, "confidence": 0.5, "source": "rules"}
    word = re.sub(r"[^a-z]", "", t)
    if word in COMMANDS and len(t.split()) == 1:
        out.update(intent=COMMANDS[word], confidence=1.0)
        return out
    for intent, words in KEYWORDS:
        if _has(t, words):
            out["intent"] = intent
            break
    for ptype, words in TYPE_WORDS.items():
        if _has(t, words):
            out["place_type"] = ptype
            break

    from . import places as places_agent  # local import: avoids a cycle at module load
    place_id = places_agent.find_by_name(text)
    found = route_agent.find_places_in_text(text)
    if place_id:
        out["place_name"] = place_id
        if out["intent"] == "unknown" and len(found) < 2:
            out["intent"] = "place_details"

    norm = route_agent.norm(text)
    if len(found) >= 2:
        a, b = found[0], found[1]
        if re.search(rf"\bfrom {re.escape(route_agent.norm(b))}", norm) or f"{data_ta(b)}இருந்து" in text.replace(" ", ""):
            a, b = b, a
        out["from"], out["to"] = a, b
    elif len(found) == 1:
        if re.search(r"\b(from|at|stuck at|near)\b", norm) and out["intent"] in ("sos", "unknown", "places_open_now"):
            out["from"] = found[0]
        else:
            out["to"] = found[0]
    if out["intent"] == "unknown" and (out["to"] or out["from"]):
        out["intent"] = "plan_trip"
    if out["intent"] == "unknown" and out["place_type"]:
        out["intent"] = "places_open_now"
    if out["intent"] != "unknown":
        out["confidence"] = 0.8 if (out["to"] or out["intent"] not in ("plan_trip",)) else 0.6
    return out


def data_ta(name):
    from .. import data
    return data.area_ta(name)


def validate(obj) -> dict:
    """Return a normalized intake dict, or None if the LLM output is not usable."""
    if not isinstance(obj, dict) or obj.get("intent") not in INTENTS:
        return None
    clean = {}
    for k in ("from", "to", "place_name"):
        v = obj.get(k)
        if v is not None and not isinstance(v, str):
            return None
        clean[k] = v.strip()[:60] if isinstance(v, str) and v.strip() else None
    time = obj.get("time")
    if time is not None and not (isinstance(time, str) and (time == "now" or re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", time))):
        time = parse_time(time) if isinstance(time, str) else None
    wc = obj.get("with_child", False)
    if not isinstance(wc, bool):
        return None
    pt = obj.get("place_type")
    conf = obj.get("confidence", 0.7)
    clean.update(
        intent=obj["intent"], time=time, with_child=wc,
        lang=obj.get("lang") if obj.get("lang") in LANGS else None,
        place_type=pt if pt in PLACE_TYPES else None,
        confidence=float(conf) if isinstance(conf, (int, float)) else 0.7,
    )
    return clean


def _gemini(text: str):
    model = config.env("GEMINI_MODEL") or "gemini-2.5-flash"
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0},
    }
    r = httpx.post(GEMINI_URL.format(model=model), json=body,
                   headers={"x-goog-api-key": config.env("GEMINI_API_KEY")}, timeout=10)
    r.raise_for_status()
    parts = r.json()["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts)


def parse(text: str, names=(), llm=None) -> dict:
    """Parse text. `llm` can be injected in tests: a callable(text) -> raw string."""
    safe_text = redact(text or "", names)
    if not safe_text.strip():
        return {**rule_parse(""), "intent": "unknown", "fallback": True, "reason": "empty"}
    call = llm or (_gemini if config.has("gemini") else None)
    if call is None:
        return rule_parse(safe_text)
    try:
        raw = call(safe_text)
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as e:
        return {**rule_parse(safe_text), "source": "rules", "llm_error": type(e).__name__}
    try:
        obj = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
    except (json.JSONDecodeError, AttributeError):
        obj = None
    parsed = validate(obj)
    if parsed is None:
        return {"intent": "unknown", "from": None, "to": None, "time": None, "with_child": False,
                "lang": detect_lang(text), "place_type": None, "place_name": None, "confidence": 0.0,
                "source": "gemini", "fallback": True, "reason": "llm_invalid_json"}
    parsed["lang"] = parsed["lang"] or detect_lang(text)
    parsed["source"] = "gemini"
    if parsed.get("place_name"):
        from . import places as places_agent
        parsed["place_name"] = places_agent.find_by_name(parsed["place_name"])  # only real place ids
    return parsed
