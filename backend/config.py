"""Settings: reads .env, never exposes key values.

A service is "real" only when all of its keys are present; otherwise it runs
as a mock. A missing key never raises.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

load_dotenv(ROOT / ".env")

SERVICE_KEYS = {
    "gemini": ["GEMINI_API_KEY"],
    "sarvam": ["SARVAM_API_KEY"],
    "twilio": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"],
    "razorpay": ["RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET"],
    "maptiler": ["MAPTILER_KEY"],
    "supabase": ["SUPABASE_URL", "SUPABASE_SERVICE_KEY"],  # backend store (service key, server only)
    "supabase_public": ["SUPABASE_URL", "SUPABASE_ANON_KEY"],  # frontend read-only
    "fast2sms": ["FAST2SMS_API_KEY"],
    "textbee": ["TEXTBEE_API_KEY", "TEXTBEE_DEVICE_ID"],
    "n8n": ["N8N_WEBHOOK_URL"],
    "n8n_orchestrator": ["N8N_ORCHESTRATOR_URL"],
}

SMS_PROVIDERS = ("mock", "twilio", "fast2sms", "textbee")
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"  # gemini-2.5-flash returns 404 for new keys


def env(name: str) -> str:
    return (os.getenv(name) or "").strip()


def has(service: str) -> bool:
    return all(env(k) for k in SERVICE_KEYS[service])


def demo_mode() -> bool:
    return env("DEMO_MODE").lower() not in ("false", "0", "no")


def razorpay_mode() -> str:
    """'test' only with rzp_test_ keys. Live keys are refused (mock instead)."""
    if not has("razorpay"):
        return "mock"
    return "test" if env("RAZORPAY_KEY_ID").startswith("rzp_test_") else "refused_live"


def assert_safe_to_start():
    """Refuse to run with a live Razorpay key. Names only in the message."""
    if env("RAZORPAY_KEY_ID").startswith("rzp_live_"):
        raise RuntimeError("RAZORPAY_KEY_ID is a LIVE key (rzp_live_). SafePath runs Razorpay in TEST mode only.")


def sms_provider() -> str:
    """Selected SMS provider, or 'mock' when unset/unknown or its keys are missing."""
    name = env("SMS_PROVIDER").lower() or ("twilio" if has("twilio") else "mock")
    if name not in SMS_PROVIDERS or (name != "mock" and not has(name)):
        return "mock"
    return name


def services_status() -> dict:
    """real / mock per service. Never includes key values."""
    status = {name: "real" if has(name) else "mock" for name in SERVICE_KEYS}
    rp = razorpay_mode()
    status["razorpay"] = {"test": "real (test mode)", "mock": "mock", "refused_live": "mock (live key refused)"}[rp]
    status["maptiler"] += " (frontend map)"
    status["sms_provider"] = sms_provider()
    status["public_backend_url"] = "set" if env("PUBLIC_BACKEND_URL") else "missing"
    return status
