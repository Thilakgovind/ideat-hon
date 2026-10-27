"""Key check for SafePath. Prints key NAMES only: OK / MISSING / FAILED.

    python -m backend.check_keys          # format check + live checks
    python -m backend.check_keys --offline  # format check + presence only
    python -m backend.check_keys --env-file .env.txt  # check another file

FAILED means a real, cheap API call was rejected. Values, URLs that carry keys,
and raw error text are never printed (errors can echo the request URL).
"""
import re
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

from backend import config

ENV_FILE = config.ROOT / ".env"
TIMEOUT = 10

EXPECTED = [
    "GEMINI_API_KEY", "SARVAM_API_KEY",
    "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER",
    "RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET",
    "MAPTILER_KEY",
    "SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_KEY",
    "SMS_PROVIDER", "FAST2SMS_API_KEY", "TEXTBEE_API_KEY", "TEXTBEE_DEVICE_ID",
    "N8N_WEBHOOK_URL", "N8N_ORCHESTRATOR_URL", "PUBLIC_BACKEND_URL",
    "DEMO_MODE",
]
OPTIONAL = {"N8N_ORCHESTRATOR_URL", "FAST2SMS_API_KEY", "TEXTBEE_API_KEY", "TEXTBEE_DEVICE_ID",
            "PUBLIC_BACKEND_URL", "GEMINI_MODEL", "DEMO_CONTACT_PHONE_1", "DEMO_CONTACT_PHONE_2", "SUPABASE_DB_URL", "TEXTBEE_WEBHOOK_SECRET"}
NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
# A label is printed only if it cannot be a secret (letters/spaces/punctuation, no digits, short).
SAFE_LABEL_RE = re.compile(r"^[A-Za-z _:.\-]{1,30}$")


def _label(text: str) -> str:
    text = text.strip()
    return f'"{text}"' if SAFE_LABEL_RE.match(text) else "(hidden - may contain a value)"


# ---------------------------------------------------------------- format check
def lint_env(path: Path = ENV_FILE) -> list:
    """Return (line_no, label, problem) tuples. Never includes values."""
    issues, seen = [], {}
    twin = path.with_name(path.name + ".txt")
    if twin.exists():
        issues.append((0, twin.name, f"exists - Windows may have hidden '.txt'. The app reads {path.name}, "
                                     f"so rename {twin.name} to {path.name} (or merge them)"))
    if not path.exists():
        return issues + [(0, path.name, "file not found (copy .env.example to .env)")]
    for no, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        if "=" not in raw:
            issues.append((no, _label(raw), "no NAME=value (stray label or pasted value?)"))
            continue
        name_part, value = raw.split("=", 1)
        name = name_part.strip()
        if name.startswith("export "):
            name = name[7:].strip()
        if name_part != name_part.lstrip():
            issues.append((no, name if NAME_RE.match(name) else _label(name), "space before name"))
        if name_part != name_part.rstrip():
            issues.append((no, name if NAME_RE.match(name) else _label(name), "space between name and ="))
        if not NAME_RE.match(name):
            issues.append((no, _label(name), "invalid name (use CAPS_WITH_UNDERSCORES)"))
            continue
        if name in seen:
            issues.append((no, name, f"duplicate (first on line {seen[name]})"))
        seen.setdefault(name, no)
        v = value.strip()
        quoted = len(v) >= 2 and v[0] == v[-1] and v[0] in "'\""
        if value != value.lstrip():
            issues.append((no, name, "space after ="))
        if not quoted and re.search(r"\s", v.split(" #")[0].strip() if v else ""):
            issues.append((no, name, "value contains spaces"))
        if v and v[0] in "'\"" and not quoted:
            issues.append((no, name, "unmatched quote"))
        if name not in EXPECTED and name not in OPTIONAL:
            issues.append((no, name, "unknown name (typo?)"))
    for name in EXPECTED:
        if name not in seen and name not in OPTIONAL:
            issues.append((0, name, "not in .env"))
    return issues


# ---------------------------------------------------------------- live checks
def _status(fn) -> tuple:
    """Run one check; map any error to a safe reason string."""
    try:
        return fn()
    except httpx.TimeoutException:
        return "FAILED", "timeout"
    except httpx.HTTPError as e:
        return "FAILED", f"network error ({type(e).__name__})"
    except Exception as e:  # noqa: BLE001 - never echo the message, it may contain a value
        return "FAILED", type(e).__name__


def _http(r) -> tuple:
    if r.status_code < 300:
        return "OK", ""
    if r.status_code in (401, 403):
        return "FAILED", f"HTTP {r.status_code} (key rejected)"
    return "FAILED", f"HTTP {r.status_code}"


def check_gemini():
    """Tiny real generate call (1 output token)."""
    model = config.env("GEMINI_MODEL") or config.DEFAULT_GEMINI_MODEL
    r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                   headers={"x-goog-api-key": config.env("GEMINI_API_KEY")},
                   json={"contents": [{"parts": [{"text": "Reply with: ok"}]}],
                         "generationConfig": {"maxOutputTokens": 5, "temperature": 0}},
                   timeout=TIMEOUT)
    status, why = _http(r)
    return status, (f"model {model}" if status == "OK" else why + (" (check GEMINI_MODEL)" if r.status_code == 404 else ""))


def check_sarvam():
    r = httpx.post("https://api.sarvam.ai/text-to-speech",
                   headers={"api-subscription-key": config.env("SARVAM_API_KEY")},
                   json={"text": "வணக்கம்", "target_language_code": "ta-IN"}, timeout=TIMEOUT)
    status, why = _http(r)
    return status, ("tiny Tamil TTS" if status == "OK" else why)


def check_twilio():
    sid = config.env("TWILIO_ACCOUNT_SID")
    r = httpx.get(f"https://api.twilio.com/2010-04-01/Accounts/{sid}.json",
                  auth=(sid, config.env("TWILIO_AUTH_TOKEN")), timeout=TIMEOUT)
    status, why = _http(r)
    if status == "OK":
        acct = r.json()
        why = f"account {acct.get('status', '?')}, type {acct.get('type', '?')}"
    return status, why


def check_razorpay():
    kid = config.env("RAZORPAY_KEY_ID")
    if kid.startswith("rzp_live_"):
        return "FAILED", "LIVE key refused - use rzp_test_ only"
    if not kid.startswith("rzp_test_"):
        return "FAILED", "key id must start with rzp_test_"
    return _http(httpx.get("https://api.razorpay.com/v1/orders", params={"count": 1},
                           auth=(kid, config.env("RAZORPAY_KEY_SECRET")), timeout=TIMEOUT))


def check_maptiler():
    url, params = "https://api.maptiler.com/maps/streets-v2/style.json", {"key": config.env("MAPTILER_KEY")}
    status, why = _http(httpx.get(url, params=params, timeout=TIMEOUT))
    if status == "FAILED" and "403" in why:
        # Keys can be restricted to browser origins; retry as the local frontend would.
        r = httpx.get(url, params=params, headers={"Origin": "http://localhost:5173",
                                                   "Referer": "http://localhost:5173/"}, timeout=TIMEOUT)
        if r.status_code < 300:
            return "OK", "origin-restricted key (works from localhost:5173)"
    return status, why


def _supabase(key_name):
    url = config.env("SUPABASE_URL").rstrip("/")
    if not url.startswith("https://"):
        return "FAILED", "SUPABASE_URL must start with https://"
    key = config.env(key_name)
    return _http(httpx.get(f"{url}/auth/v1/settings", headers={"apikey": key}, timeout=TIMEOUT))


def check_fast2sms():
    return _http(httpx.post("https://www.fast2sms.com/dev/wallet",
                            headers={"authorization": config.env("FAST2SMS_API_KEY")}, timeout=TIMEOUT))


def check_textbee():
    r = httpx.get("https://api.textbee.dev/api/v1/gateway/devices",
                  headers={"x-api-key": config.env("TEXTBEE_API_KEY")}, timeout=TIMEOUT)
    status, why = _http(r)
    if status != "OK":
        return status, why
    body = r.json()
    devices = body.get("data", body) if isinstance(body, dict) else body
    ids = {str(d.get("_id") or d.get("id")) for d in devices if isinstance(d, dict)} if isinstance(devices, list) else set()
    if config.env("TEXTBEE_DEVICE_ID") not in ids:
        return "FAILED", f"key OK, but TEXTBEE_DEVICE_ID is not one of your {len(ids)} device(s)"
    return "OK", f"key OK, device found ({len(ids)} device(s))"


def _url_set(name):
    v = config.env(name)
    return ("OK", "URL set (not called)") if v.startswith(("http://", "https://")) else ("FAILED", "not an http(s) URL")


def _sms_provider():
    v = config.env("SMS_PROVIDER").lower()
    if v in config.SMS_PROVIDERS:
        return "OK", f"{v} (active: {config.sms_provider()})"
    return "FAILED", "must be mock | twilio | fast2sms | textbee"


def _demo_mode():
    return "OK", "true" if config.demo_mode() else "false"


# (names that must be present, check fn or None, keys checked by that fn)
CHECKS = [
    (["GEMINI_API_KEY"], check_gemini),
    (["SARVAM_API_KEY"], check_sarvam),
    (["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"], check_twilio),
    (["TWILIO_PHONE_NUMBER"], None),
    (["RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET"], check_razorpay),
    (["MAPTILER_KEY"], check_maptiler),
    (["SUPABASE_URL", "SUPABASE_ANON_KEY"], lambda: _supabase("SUPABASE_ANON_KEY")),
    (["SUPABASE_SERVICE_KEY"], lambda: _supabase("SUPABASE_SERVICE_KEY")),
    (["SMS_PROVIDER"], _sms_provider),
    (["FAST2SMS_API_KEY"], check_fast2sms),
    (["TEXTBEE_API_KEY", "TEXTBEE_DEVICE_ID"], check_textbee),
    (["N8N_WEBHOOK_URL"], lambda: _url_set("N8N_WEBHOOK_URL")),
    (["N8N_ORCHESTRATOR_URL"], lambda: _url_set("N8N_ORCHESTRATOR_URL")),
    (["PUBLIC_BACKEND_URL"], lambda: _url_set("PUBLIC_BACKEND_URL")),
    (["DEMO_MODE"], _demo_mode),
    (["DEMO_CONTACT_PHONE_1"], None),
    (["DEMO_CONTACT_PHONE_2"], None),
]


def run_checks(offline: bool = False) -> list:
    """Return (names, status, note) rows. Status is OK / MISSING / FAILED."""
    rows = []
    for names, fn in CHECKS:
        needed = names + (["SUPABASE_URL"] if names == ["SUPABASE_SERVICE_KEY"] else [])
        missing = [n for n in needed if not config.env(n)]
        if missing:
            note = "optional" if all(n in OPTIONAL for n in names) else ""
            rows.append((", ".join(names), "MISSING", note or ("needs " + ", ".join(missing))))
        elif fn is None or offline:
            rows.append((", ".join(names), "OK", "present" + (" (not called)" if fn else "")))
        else:
            status, note = _status(fn)
            rows.append((", ".join(names), status, note))
    return rows


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    offline = "--offline" in argv
    env_file = ENV_FILE
    if "--env-file" in argv:
        env_file = Path(argv[argv.index("--env-file") + 1]).resolve()
        load_dotenv(env_file, override=True)

    print(f"== {env_file.name} format ==")
    issues = lint_env(env_file)
    if not issues:
        print("  no problems found")
    for no, label, problem in issues:
        print(f"  line {no:>3}  {label}: {problem}" if no else f"  {label}: {problem}")

    print("\n== keys ==" + (" (offline: presence only)" if offline else ""))
    rows = run_checks(offline)
    width = max(len(r[0]) for r in rows)
    for names, status, note in rows:
        print(f"  {names.ljust(width)}  {status:<7} {note}")
    failed = [r for r in rows if r[1] == "FAILED"]
    print(f"\n{sum(r[1] == 'OK' for r in rows)} OK, {sum(r[1] == 'MISSING' for r in rows)} MISSING, "
          f"{len(failed)} FAILED. Missing keys run as mock (demo mode).")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
