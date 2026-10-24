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
    "supabase": ["SUPABASE_URL", "SUPABASE_ANON_KEY"],
    "n8n": ["N8N_WEBHOOK_URL"],
}


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


def services_status() -> dict:
    status = {}
    for name in SERVICE_KEYS:
        status[name] = "real" if has(name) else "mock"
    rp = razorpay_mode()
    status["razorpay"] = {"test": "real (test mode)", "mock": "mock", "refused_live": "mock (live key refused)"}[rp]
    # Not used by the V1 backend: storage is in memory, maps are drawn in the frontend.
    status["supabase"] += " (V1 uses in-memory store)"
    status["maptiler"] += " (used by frontend only)"
    return status
