"""Avvai's sports-support guidance. No bookings, diagnoses or funding promises."""
import json
import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from . import config
from .guardrails import redact
from . import local_model
from .athlete_support import match as support_policy

def supported_answer(body):
    policy = support_policy(body.text)
    if not policy or policy['policy_id'] in ('fees','journey','opportunity'):
        return None
    return {**policy, 'provider':'support_policy', 'href':LINKS[policy['module']],
            'sample':False, 'orchestration':'guardrail',
            'answer_levels':{'now':policy['reply'], 'next':'You choose whether to open support or speak with a qualified professional.',
                             'privacy':'No health history was saved, and nothing was sent to a coach.'}}

router = APIRouter()
LINKS = {"opportunities": "/veeramangai/opportunities", "funding": "/veeramangai/funding", "travel": "/veeramangai/travel", "support": "/veeramangai/support"}

@router.get('/api/veeramangai/catalog')
def sports_catalog():
    from .sports_store import read
    from .seed.sports_sample import PUBLIC_TABLES
    result, storage = {}, {}
    for table in PUBLIC_TABLES:
        result[table], storage[table] = read(table)
    districts = {d['id']: d['name'] for d in result['vm_districts']}
    sports = {s['id']: s['name'] for s in result['vm_sports']}
    opportunities = [{**o, 'district': districts.get(o['district_id'], ''),
                      'sport': sports.get(o['sport_id'], '')} for o in result['vm_opportunities']]
    return {'opportunities': opportunities, 'districts': result['vm_districts'],
            'sports': result['vm_sports'], 'resources': result['vm_resources'], 'storage': storage,
            'notice': 'Sample data for demo. Sample events accept no applications; organizations are fictional.'}

class Message(BaseModel):
    text: str = Field(min_length=1, max_length=1500)
    lang: str = "en"

def classify(text):
    safe = redact(text).lower()
    groups = {"opportunities": ("trial", "tournament", "camp", "opportunit", "போட்டி"),
              "funding": ("fund", "fee", "money", "equipment", "பணம்"),
              "travel": ("travel", "bus", "companion", "பயணம்"),
              "support": ("rest", "coach", "private", "period", "pain", "support", "ஓய்வு")}
    return next((key for key, words in groups.items() if any(w in safe for w in words)), "opportunities")

@router.post('/api/veeramangai/assistant')
def assistant(body: Message):
    guarded = supported_answer(body)
    if guarded:
        return guarded
    if local_model.enabled():
        return {**chat(body), 'orchestration': 'local_backend'}
    from urllib.parse import urlparse
    url = config.env('VM_N8N_GUIDE_URL')
    parsed = urlparse(url)
    topic = classify(body.text)
    lang = 'ta' if body.lang == 'ta' else 'en'
    if parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.password:
        try:
            r = httpx.post(url, json={'topic': topic, 'lang': lang}, timeout=20, follow_redirects=False)
            r.raise_for_status()
            result = r.json()
            if (isinstance(result.get('reply'), str) and 0 < len(result['reply']) < 1500
                    and result.get('module') == topic):
                return {'reply': result['reply'], 'module': topic, 'href': LINKS[topic],
                        'provider': result.get('provider', 'fallback'), 'sample': True,
                        'orchestration': 'n8n'}
        except (httpx.HTTPError, ValueError, TypeError, AttributeError):
            pass
    return {**chat(body), 'orchestration': 'backend_fallback'}

@router.post('/api/veeramangai/chat')
def chat(body: Message):
    guarded = supported_answer(body)
    if guarded:
        return guarded
    safe = redact(body.text)
    # Retain only recognised task words; free-text names and health details never leave this server.
    groups = {"opportunities": ("trial", "tournament", "camp", "opportunit", "போட்டி"),
              "funding": ("fund", "fee", "money", "equipment", "பணம்"),
              "travel": ("travel", "bus", "companion", "பயணம்"),
              "support": ("rest", "coach", "private", "period", "pain", "support", "ஓய்வு")}
    module = next((key for key, words in groups.items() if any(w in safe.lower() for w in words)), "opportunities")
    replies = {"opportunities": "Choose an opportunity, review its eligibility and deadline, then select ‘I want to attend’. Listings here are samples; confirm the original notice before applying.",
               "funding": "You can prepare a request for entry fees or equipment. The current request flow is a local demo: no sponsor has received it and no payment is taken.",
               "travel": "You can prepare a travel-support request and choose what help you need. A real coordinator must confirm a group or companion before you rely on an arrangement.",
               "support": "You can ask for rest, a lighter session or a private conversation without giving a reason. You decide what to share. The demo does not send anything to a coach."}
    tamil = {"opportunities": "மாதிரி போட்டிகளைப் பார்க்கலாம். தகுதி மற்றும் கடைசித் தேதியை உண்மையான அறிவிப்பில் சரிபார்த்த பிறகே விண்ணப்பிக்கவும்.", "funding": "கட்டணம் அல்லது உபகரண உதவிக்கான கோரிக்கையைத் தயாரிக்கலாம். இது மாதிரி மட்டும்; யாருக்கும் அனுப்பப்படவில்லை.", "travel": "பயண உதவிக்கான கோரிக்கையைத் தயாரிக்கலாம். உண்மையான ஒருங்கிணைப்பாளர் உறுதிசெய்த பிறகே பயண ஏற்பாட்டை நம்பவும்.", "support": "காரணம் சொல்லாமல் ஓய்வு அல்லது தனிப்பட்ட உரையாடலைக் கேட்கலாம். இது மாதிரி மட்டும்; பயிற்சியாளருக்கு அனுப்பப்படவில்லை."}
    reply = tamil[module] if body.lang == "ta" else replies[module]
    provider = "fallback"
    if local_model.enabled():
        generated = local_model.generate(reply, body.lang)
        return {**(generated or {'reply': reply, 'provider': 'fallback'}),
                'module': module, 'href': LINKS[module], 'sample': True}
    if config.has("gemini"):
        try:
            prompt = f"You are Avvai, a concise Tamil Nadu women athletes app guide. Explain this verified app instruction in {'Tamil' if body.lang == 'ta' else 'English'}, warmly in at most 70 words. Do not add events, organizations, medical advice, funding, or claims of actions taken. Return JSON with only a reply string. Instruction: {reply}"
            r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/{config.env('GEMINI_MODEL') or config.DEFAULT_GEMINI_MODEL}:generateContent",
                           headers={"x-goog-api-key": config.env("GEMINI_API_KEY")}, json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 300}}, timeout=8)
            r.raise_for_status()
            parsed = json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
            if isinstance(parsed.get("reply"), str) and 0 < len(parsed["reply"]) < 1500:
                reply, provider = parsed["reply"], "gemini"
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
            pass
    return {"reply": reply, "provider": provider, "module": module, "href": LINKS[module], "sample": True}


@router.post('/api/veeramangai/voice')
async def voice_chat(audio: UploadFile = File(...), lang: str = Form('ta')):
    import asyncio
    from .agents import voice
    raw = await audio.read(8 * 1024 * 1024 + 1)
    if len(raw) > 8 * 1024 * 1024:
        raise HTTPException(413, 'Recording too large. Please record a shorter question.')
    heard = await asyncio.to_thread(voice.stt, raw, audio.filename or 'speech.webm', audio.content_type or 'audio/webm', lang)
    if heard.get('provider') != 'sarvam' or not heard.get('text'):
        raise HTTPException(503, 'Speech recognition is unavailable. Please type your question.')
    result = await asyncio.to_thread(assistant, Message(text=heard['text'][:1500], lang=lang))
    spoken = await asyncio.to_thread(voice.tts, result['reply'], lang)
    return {**result, 'transcript': heard['text'], 'audio_base64': spoken.get('audio_base64'),
            'stt_provider': heard['provider'], 'tts_provider': spoken['provider']}
