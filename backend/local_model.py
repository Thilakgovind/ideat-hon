"""Local-only Ollama adapter. No credentials or athlete text in prompts."""
import json
from urllib.parse import urlparse
import httpx
from . import config

def enabled():
    return config.env('AVVAI_MODEL_PROVIDER').lower() == 'ollama'

def generate(instruction, lang):
    base = config.env('OLLAMA_BASE_URL') or 'http://127.0.0.1:11434'
    parsed = urlparse(base)
    if parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1','localhost','::1') or parsed.username or parsed.password:
        return None
    model = config.env('OLLAMA_MODEL') or 'qwen2.5:3b'
    try:
        r = httpx.post(base.rstrip('/')+'/api/chat', json={
            'model': model, 'stream': False, 'format': 'json', 'keep_alive': '30m',
            'options': {'temperature': 0.2, 'num_predict': 220, 'num_ctx': 2048},
            'messages': [
                {'role':'system','content': 'You are Avvai, a Tamil Nadu women athletes app guide. Rewrite ONLY the supplied app instruction warmly and briefly. Do not invent events, facts, medical advice, approvals, messages sent or payments. Return JSON with one reply string, under 70 words.'},
                {'role':'user','content': f'Language: {"Tamil" if lang == "ta" else "English"}. Instruction: {instruction}'}]},
            timeout=90, follow_redirects=False)
        r.raise_for_status()
        data = r.json()
        result = json.loads(data['message']['content'])
        reply = result.get('reply')
        if data.get('done') and isinstance(reply,str) and 0 < len(reply.strip()) < 1500:
            return {'reply':reply.strip(),'provider':'ollama','model':model}
    except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError):
        pass
    return None
