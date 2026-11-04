"""Bounded Avvai guidance harness. No tools or side effects are granted to chat."""
import re
import unicodedata

from .guardrails import redact

INJECTION = re.compile(
    r'ignore\s+(?:all\s+|previous\s+|your\s+)?(?:instructions|rules|privacy)|'
    r'reveal\s+(?:the\s+)?(?:system|secrets?|credentials?)|'
    r'(?:system|developer)\s*(?:message|prompt)\s*:|'
    r'approve\s+(?:\w+\s+){0,3}automatically|'
    r'(?:bypass|disable)\s+(?:\w+\s+){0,2}(?:consent|guardrails|privacy)|'
    r'vidhigalai\s+maranthu|விதிகளை\s*புறக்கணி', re.I)


def inspect_input(text):
    """Heuristic signal only; backend authority never depends on detection."""
    normalized = unicodedata.normalize('NFKC', text)
    normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Cf')
    return bool(INJECTION.search(normalized))


def refusal():
    return {'reply': 'I cannot bypass privacy, reveal credentials, approve requests or execute payments from chat. Use the authenticated workflow and review the action before confirming it.',
            'policy_id': 'injection', 'module': 'support', 'href': '/veeramangai/support',
            'provider': 'harness', 'sample': False, 'orchestration': 'guardrail'}


def validate_reply(candidate, canonical):
    """Only a verified canonical answer can pass without a semantic reviewer.

    Different paraphrases fall back, even when apparently harmless: regex checks
    cannot prove that a generated medical/action/factual claim is supported.
    Applies equally to local models, Gemini and untrusted n8n output.
    """
    if not isinstance(candidate, str) or len(candidate) > 1500:
        return canonical, False
    if candidate.strip() != canonical.strip() or redact(candidate) != candidate:
        return canonical, False
    return candidate.strip(), True


def guidance_result(result, canonical):
    """Preserve server-owned metadata, and never accept model-owned actions."""
    reply, accepted = validate_reply(result.get('reply') if isinstance(result, dict) else None, canonical)
    return {'reply': reply, 'provider': result.get('provider', 'fallback') if accepted else 'fallback',
            'harness': {'version': 1, 'output': 'verified' if accepted else 'canonical_fallback',
                        'tools_allowed': False}}
