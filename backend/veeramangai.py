"""Avvai's sports-support guidance. No bookings, diagnoses or funding promises."""
import json
import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from . import config
from .guardrails import redact
from . import local_model, avvai_harness
from .athlete_support import match as support_policy

def supported_answer(body):
    policy = support_policy(body.text)
    if not policy or policy['policy_id'] in ('fees','journey','opportunity'):
        return avvai_harness.refusal() if avvai_harness.inspect_input(body.text) else None
    return {**policy, 'provider':'support_policy', 'href':LINKS[policy['module']],
            'sample':False, 'orchestration':'guardrail',
            'answer_levels':{'now':policy['reply'], 'next':'You choose whether to open support or speak with a qualified professional.',
                             'privacy':'No health history was saved, and nothing was sent to a coach.'}}

router = APIRouter()
LINKS = {"opportunities": "/veeramangai/opportunities", "funding": "/veeramangai/funding", "travel": "/veeramangai/travel", "support": "/veeramangai/support"}

@router.get('/api/veeramangai/digilocker/start')
def digilocker_start():
    """Return a transparent manual/demo entry point until API Setu approves OAuth."""
    return {
        'mode': 'manual_demo',
        'connected': False,
        'provider_url': 'https://www.digilocker.gov.in/',
        'message': 'DigiLocker app authorization is pending API Setu approval. No document was accessed or stored.',
        'next': 'Use the official DigiLocker site manually, or configure approved API Setu OAuth credentials.'
    }

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


class OpportunityMatch(BaseModel):
    sport: str | None = Field(None, max_length=80)
    district: str | None = Field(None, max_length=80)
    kind: str | None = Field(None, max_length=40)
    query: str | None = Field(None, max_length=200)
    limit: int = Field(5, ge=1, le=20)


@router.post('/api/veeramangai/opportunities/match')
def match_opportunities(body: OpportunityMatch):
    from .opportunity_match import match
    return {'matches': match(sport=body.sport, district=body.district, kind=body.kind,
                             query=body.query, limit=body.limit),
            'source': 'supabase_or_sample_fallback',
            'notice': 'Sample opportunities are fictional and cannot accept applications.'}


class PartnerMatch(BaseModel):
    offer_type: str | None = Field(None, max_length=40)
    sport_id: str | None = Field(None, max_length=80)
    district_id: str | None = Field(None, max_length=80)
    query: str | None = Field(None, max_length=200)
    limit: int = Field(5, ge=1, le=20)


@router.post('/api/veeramangai/partners/match')
def match_partner_offers(body: PartnerMatch):
    from .partner_match import match
    return {'matches': match(offer_type=body.offer_type, sport_id=body.sport_id,
                             district_id=body.district_id, query=body.query, limit=body.limit),
            'notice': 'Only verified open partner offers are returned. No offer is claimed by this search.'}

class NSSMatch(BaseModel):
    district_id: str | None = Field(None, max_length=80)
    activity_type: str | None = Field(None, max_length=80)
    query: str | None = Field(None, max_length=200)
    limit: int = Field(10, ge=1, le=20)

@router.post('/api/veeramangai/nss/match')
def match_nss(body: NSSMatch):
    from .nss_support import match
    return {'matches': match(district_id=body.district_id, activity_type=body.activity_type,
                             query=body.query, limit=body.limit),
            'notice': 'NSS units are shown only after institution verification. Sample rows cannot be joined.'}

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
    from urllib.parse import urlparse
    url = config.env('VM_N8N_GUIDE_URL')
    parsed = urlparse(url)
    topic = classify(body.text)
    lang = 'ta' if body.lang == 'ta' else 'en'
    if parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.password:
        try:
            r = httpx.post(url, json={'topic': topic, 'lang': lang}, timeout=65, follow_redirects=False)
            r.raise_for_status()
            result = r.json()
            if (isinstance(result.get('reply'), str) and 0 < len(result['reply']) < 1500
                    and result.get('module') == topic):
                return {**avvai_harness.guidance_result(result, chat_canonical(topic, lang)), 'module': topic, 'href': LINKS[topic],
                        'sample': True,
                        'orchestration': 'n8n'}
        except (httpx.HTTPError, ValueError, TypeError, AttributeError):
            pass
    return {**chat(body), 'orchestration': 'backend_fallback'}


def chat_canonical(module, lang):
    replies = {"opportunities": "Choose an opportunity, review its eligibility and deadline, then select ‘I want to attend’. Listings here are samples; confirm the original notice before applying.",
               "funding": "You can prepare a request for entry fees or equipment. The current request flow is a local demo: no sponsor has received it and no payment is taken.",
               "travel": "You can prepare a travel-support request and choose what help you need. A real coordinator must confirm a group or companion before you rely on an arrangement.",
               "support": "You can ask for rest, a lighter session or a private conversation without giving a reason. You decide what to share. The demo does not send anything to a coach."}
    tamil = {"opportunities": "மாதிரி போட்டிகளைப் பார்க்கலாம். தகுதி மற்றும் கடைசித் தேதியை உண்மையான அறிவிப்பில் சரிபார்த்த பிறகே விண்ணப்பிக்கவும்.", "funding": "கட்டணம் அல்லது உபகரண உதவிக்கான கோரிக்கையைத் தயாரிக்கலாம். இது மாதிரி மட்டும்; யாருக்கும் அனுப்பப்படவில்லை.", "travel": "பயண உதவிக்கான கோரிக்கையைத் தயாரிக்கலாம். உண்மையான ஒருங்கிணைப்பாளர் உறுதிசெய்த பிறகே பயண ஏற்பாட்டை நம்பவும்.", "support": "காரணம் சொல்லாமல் ஓய்வு அல்லது தனிப்பட்ட உரையாடலைக் கேட்கலாம். இது மாதிரி மட்டும்; பயிற்சியாளருக்கு அனுப்பப்படவில்லை."}
    reply = tamil[module] if lang == "ta" else replies[module]
    return reply

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
    matches = []
    if module == 'opportunities':
        from .opportunity_match import match
        matches = match(query=safe, limit=5)
    reply = chat_canonical(module, body.lang)
    provider = "fallback"
    if local_model.enabled():
        generated = local_model.generate(reply, body.lang)
        return {**avvai_harness.guidance_result(generated, reply),
                'module': module, 'href': LINKS[module], 'matches': matches, 'sample': True}
    if config.has("gemini"):
        try:
            prompt = f"You are Avvai, a concise Tamil Nadu women athletes app guide. Explain this verified app instruction in {'Tamil' if body.lang == 'ta' else 'English'}, warmly in at most 70 words. Do not add events, organizations, medical advice, funding, or claims of actions taken. Return JSON with only a reply string. Instruction: {reply}"
            r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/{config.env('GEMINI_MODEL') or config.DEFAULT_GEMINI_MODEL}:generateContent",
                           headers={"x-goog-api-key": config.env("GEMINI_API_KEY")}, json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 300}}, timeout=8)
            r.raise_for_status()
            parsed = json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
            if isinstance(parsed.get("reply"), str) and 0 < len(parsed["reply"]) < 1500:
                checked = avvai_harness.guidance_result({"reply": parsed["reply"], "provider": "gemini"}, reply)
                reply, provider = checked["reply"], checked["provider"]
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
            pass
    return {"reply": reply, "provider": provider, "module": module, "href": LINKS[module],
            "matches": matches, "sample": True}


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
