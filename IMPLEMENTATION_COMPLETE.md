# SafePath: Complete Implementation Guide

**Status:** All code & specs ready  
**Target:** Build Phase 1 (SMS Core) in 6-8 hours  
**Created:** 2024-10-23

---

## Quick Summary: What You Need to Do

1. **Get 3 API keys** (35 min total) - See API_KEYS_AND_SETUP.md
   - Twilio Account SID + Auth Token + Trial Phone
   - Claude API Key
   - n8n Instance + Webhook URL

2. **Set up .env file** (5 min)
   - Copy from API_KEYS_AND_SETUP.md

3. **Test locally** (30 min)
   - Route lookup: `python agents/route_and_sakhi_lookup.py`
   - Twilio connection: Send test SMS to trial number
   - Claude API: Test Intake Agent parsing

4. **Build n8n workflow** (4 hours)
   - Follow WORKFLOW_BLUEPRINT.md (already exists)
   - 8 nodes: Webhook → Parse → Intake → Route → Sakhi → Format → Send

5. **Live test** (1 hour)
   - Send real SMS, verify reply
   - Check all edge cases

6. **Add Journey Watch** (4-6 hours, can be parallel)
   - Scheduled workflows from BACKEND_LOGIC_COMPLETE.md

7. **Build dashboard** (3-4 hours, can be parallel)
   - HTML + Python backend from BACKEND_LOGIC_COMPLETE.md

---

## Phase 1: SMS Core (6-8 hours for 2 people)

### Timeline

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| 0:00-0:35 | Get API keys & set up .env | Person A | .env file with all credentials |
| 0:35-1:05 | Test route lookup locally | Person B | ✅ Python script passes all tests |
| 1:05-1:20 | Test Claude API (test_intake.py) | Person B | ✅ Intake agent works |
| 1:20-1:50 | Create n8n instance + webhook | Person A | Webhook URL ready |
| 1:50-5:50 | Build n8n workflow (8 nodes) | Person A + B | ✅ All 8 nodes configured |
| 5:50-6:50 | Test end-to-end (5 SMS samples) | Both | ✅ All test cases pass |

### Critical Checkpoints

**Checkpoint 1 (1 hour)**
- [ ] API keys are valid (test with simple API call)
- [ ] .env file is in project root
- [ ] Route lookup script works locally

**Checkpoint 2 (2 hours)**
- [ ] n8n instance is running
- [ ] Webhook URL is accessible
- [ ] Can POST test data to webhook

**Checkpoint 3 (5 hours)**
- [ ] All 8 n8n nodes are configured
- [ ] No red error indicators in workflow
- [ ] Test messages flow through each node

**Checkpoint 4 (6.5 hours)**
- [ ] Can send SMS to Twilio number
- [ ] Get route reply within 5 seconds
- [ ] Safe point is included in reply

---

## Phase 1 Detailed Setup

### Step 1: Get API Keys (35 min)

**1.1 Twilio (15 min)**
```
1. Go to https://www.twilio.com/try-twilio
2. Create account (email + phone verification)
3. Go to Twilio Console
4. Find: Account SID (under your name)
5. Find: Auth Token (under your name)
6. Find: Phone Number (under Numbers → Manage)
   Example: +1234567890
7. Verify your personal phone number (for testing)
```

**Save to .env:**
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE=+1234567890
```

**1.2 Claude API (5 min)**
```
1. Go to https://console.anthropic.com/
2. Log in or create account
3. Click "Create API key"
4. Copy the key
```

**Save to .env:**
```
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
```

**1.3 n8n (15 min)**

**Option A: Cloud (Recommended)**
```
1. Go to https://n8n.io
2. Click "Get started"
3. Create free account
4. Create first workflow
5. At top right, click "Share" → "Public link"
6. Copy the URL
   Example: https://abc123.n8n.cloud/webhook
```

**Option B: Local**
```
1. Install Node.js if not already
2. npm install -g n8n
3. n8n start
4. Open http://localhost:5678 in browser
5. Your public URL will appear in console
```

**Save to .env:**
```
N8N_WEBHOOK_URL=https://abc123.n8n.cloud/webhook
```

---

### Step 2: Create .env File

**Create** `C:\Users\THILAK GOVIND\OneDrive\Desktop\murdermurugaveni\.env`

```
# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE=+1234567890

# Claude API
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx

# n8n
N8N_WEBHOOK_URL=https://abc123.n8n.cloud/webhook

# Phase 2 (optional for now)
# BACKEND_API_URL=http://localhost:5000
# SUPABASE_URL=optional
# SARVAM_API_KEY=optional
```

**Important:** Add `.env` to `.gitignore` (don't commit credentials!)

---

### Step 3: Test Locally (1 hour)

**3.1 Route Lookup Test**
```bash
cd C:\Users\THILAK GOVIND\OneDrive\Desktop\murdermurugaveni

python agents/route_and_sakhi_lookup.py
```

**Expected output:**
```
============================================================
TEST 1: Route lookup (T. Nagar to Nungambakkam)
============================================================
{
  "from_stop": "T. Nagar Depot",
  "to_stop": "Nungambakkam",
  "routes": [
    {
      "number": "21G",
      "is_free": true,
      "frequency_minutes": 15,
      "notes": "Free ordinary bus, runs every 15-20 min",
      "stop_sequence": ["TND", "RMN", "TEN", "NMB"],
      "operator": "MTC"
    }
  ]
}
...
```

**If successful:** ✅ All tests pass

**3.2 Claude API Test**

**Create file:** `test_intake_api.py`

```python
import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("CLAUDE_API_KEY")

# Read the system prompt
with open("agents/intake_agent_prompt.md") as f:
    system_prompt = f.read()

# Test SMS samples
test_samples = [
    "T Nagar to Nungambakkam 8 mani",
    "START",
    "REACHED",
    "anna nagar vera road evening paapa",
    "HELP stuck at teynampet"
]

for sms in test_samples:
    print(f"\n{'='*60}")
    print(f"Testing: {sms}")
    print('='*60)
    
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": API_KEY,
            "content-type": "application/json",
        },
        json={
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 500,
            "system": system_prompt,
            "messages": [{"role": "user", "content": f"Parse this SMS:\n\n{sms}"}],
        }
    )
    
    result = response.json()
    if "content" in result and len(result["content"]) > 0:
        intent_json = result["content"][0]["text"]
        parsed = json.loads(intent_json)
        print(json.dumps(parsed, indent=2))
    else:
        print("ERROR:", result)
```

**Run:**
```bash
pip install python-dotenv requests
python test_intake_api.py
```

**Expected:** All SMS are parsed correctly with intent, from, to, language fields

---

### Step 4: Build n8n Workflow

**Reference:** `WORKFLOW_BLUEPRINT.md` (already in folder)

**High-level steps:**
1. Create webhook trigger
2. Add HTTP node for Claude Intake Agent
3. Add Function node for Route Lookup
4. Add Function node for Sakhi Network Lookup
5. Add Set node to format reply
6. Add HTTP node to send SMS via Twilio
7. Test with sample webhook data

**Each node's code is in WORKFLOW_BLUEPRINT.md. Copy-paste and adapt.**

---

### Step 5: Connect Twilio → n8n

1. **Get your Twilio webhook URL** from n8n workflow (Share → Public link)
2. **Go to Twilio Console**
3. **Phone Numbers** → **Manage Numbers** → Select your trial number
4. **Messaging** → **A message comes in** → Set to `https://your-n8n-url/webhook`
5. **Save**

---

### Step 6: Test End-to-End

**Send these 5 SMS from your phone to your Twilio number:**

| SMS | Expected Reply | Verify |
|-----|---|---|
| `"T Nagar to Nungambakkam"` | 21G FREE bus, every 15 min, Lakshmi Tea Stall | ✅ or ❌ |
| `"anna nagar to central"` | 5A FREE bus info | ✅ or ❌ |
| `"START"` | "Journey Watch is ON" | ✅ or ❌ |
| `"REACHED"` | "Safe arrival recorded" | ✅ or ❌ |
| `"HELP"` | "Help alert sent" | ✅ or ❌ |

**If all pass:** 🎉 Phase 1 complete!

---

## Phase 2: Journey Watch (4-6 hours, Parallel)

**Can run while Phase 1 is being built by the other person**

### Overview
Add trip tracking: START → timer → check-in → escalate if needed

### Workflow Outline
```
User SMS "START"
  ↓
Create trip record (start_time, expected_arrival)
  ↓
Send confirmation SMS
  ↓
[DELAY 10 minutes]
  ↓
Check-in: "Are you safe?"
  ├→ User replies "REACHED": Done
  └→ No reply:
     [DELAY 15 more min]
     ↓
     Escalate: Alert trusted contacts
```

### Backend Code (Python Flask)

**Create file:** `safepath_backend.py`

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import uuid
import json

app = Flask(__name__)
CORS(app)

# In-memory trip storage (Phase 2: use Supabase)
TRIPS = {}

@app.route("/api/journey/start", methods=["POST"])
def start_journey():
    """Create a new trip."""
    data = request.json
    trip_id = str(uuid.uuid4())
    
    TRIPS[trip_id] = {
        "trip_id": trip_id,
        "user_phone": data["user_phone"],
        "from_stop": data["from_stop"],
        "to_stop": data["to_stop"],
        "bus_number": data["bus_number"],
        "start_time": datetime.utcnow().isoformat(),
        "expected_arrival": (
            datetime.utcnow() + 
            timedelta(minutes=data.get("travel_minutes", 25))
        ).isoformat(),
        "status": "in_transit",
        "reached_confirmed": False,
        "escalation_contacts": data.get("contacts", [])
    }
    
    return jsonify({"trip_id": trip_id, "status": "started"})

@app.route("/api/journey/reached", methods=["POST"])
def mark_reached():
    """User confirmed safe arrival."""
    trip_id = request.json["trip_id"]
    
    if trip_id in TRIPS:
        TRIPS[trip_id]["reached_confirmed"] = True
        TRIPS[trip_id]["status"] = "reached"
        return jsonify({"status": "confirmed"})
    
    return jsonify({"error": "Trip not found"}), 404

@app.route("/api/journey/escalate", methods=["POST"])
def escalate():
    """Send alerts to contacts."""
    data = request.json
    trip_id = data["trip_id"]
    
    if trip_id not in TRIPS:
        return jsonify({"error": "Trip not found"}), 404
    
    trip = TRIPS[trip_id]
    trip["status"] = "escalated"
    
    # Return data for n8n to send SMS to each contact
    return jsonify({
        "trip_id": trip_id,
        "user_phone": trip["user_phone"],
        "contacts": trip["escalation_contacts"],
        "message": f"""ALERT: {trip['user_phone']} has not confirmed arrival.
Route: {trip['from_stop']} → {trip['to_stop']} (Bus {trip['bus_number']})
Started: {trip['start_time']}
Contact them or call emergency services.
"""
    })

@app.route("/api/journey/status/<trip_id>", methods=["GET"])
def get_status(trip_id):
    """Check trip status."""
    trip = TRIPS.get(trip_id)
    if trip:
        return jsonify(trip)
    return jsonify({"error": "Not found"}), 404

if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

**Run:**
```bash
pip install flask flask-cors
python safepath_backend.py
# Listens on http://localhost:5000
```

### n8n Workflow Updates

**When intent == "start_trip":**
```javascript
// HTTP POST to backend
POST http://localhost:5000/api/journey/start
{
  "user_phone": "{{$node.TwilioPayload.json.From}}",
  "from_stop": "{{$node.IntakeAgent.json.from}}",
  "to_stop": "{{$node.IntakeAgent.json.to}}",
  "bus_number": "{{$node.RouteLookup.json.routes[0].number}}",
  "travel_minutes": 25,
  "contacts": ["{{$node.TrustedContacts1.json}}", "{{$node.TrustedContacts2.json}}"]
}

// Response: { trip_id: "uuid-..." }
```

**Schedule check-in (10 min delay):**
```javascript
// Create a separate workflow triggered by a Delay node
// This workflow:
// 1. Waits 10 minutes
// 2. Checks if user sent REACHED
// 3. If NO: waits 15 more, then escalates
```

---

## Phase 3: Policy Dashboard (3-4 hours, Parallel)

**See BACKEND_LOGIC_COMPLETE.md Part 6 for full code**

### Quick Setup

**1. Log request after each route lookup:**

In n8n, after successful route response:
```javascript
// HTTP POST to backend
POST http://localhost:5000/api/dashboard/log_request
{
  "from_area": "{{$node.IntakeAgent.json.from}}",
  "to_area": "{{$node.IntakeAgent.json.to}}",
  "timestamp": "{{now}}",
  "time_of_day": getTimeOfDay(new Date()),
  "language": "{{$node.IntakeAgent.json.language}}",
  "has_child": {{$node.IntakeAgent.json.has_child}},
  "route_found": {{!!$node.RouteLookup.json.routes}},
  "safe_point_found": {{!!$node.SakhiLookup.json.safe_points.length}}
}
```

**2. Backend analytics endpoint:**

Add to `safepath_backend.py`:
```python
@app.route("/api/dashboard/analytics", methods=["GET"])
def get_analytics():
    """Return aggregated, anonymized statistics."""
    # Analyze request log
    # Return top routes, peak times, safe point coverage, etc.
    return jsonify({
        "total_requests": len(requests_log),
        "top_routes": {...},
        "peak_times": {...},
        "safe_point_coverage": {...},
        "language_breakdown": {...}
    })

@app.route("/api/dashboard/log_request", methods=["POST"])
def log_request():
    """Log anonymized request."""
    data = request.json
    # Remove any identifying info, store
    requests_log.append(data)
    return jsonify({"status": "logged"})
```

**3. HTML dashboard:**

Save as `dashboard.html` (code in BACKEND_LOGIC_COMPLETE.md Part 6)

---

## All Code Files You Have

✅ **Complete and Ready:**
1. `SafePath_Refocused_Brief_v2.pdf` — Full project vision
2. `README.md` — Project overview
3. `SETUP_GUIDE.md` — Original build instructions
4. `BUILD_STATUS.md` — Progress tracking
5. `API_KEYS_AND_SETUP.md` — What keys you need (NEW)
6. `BACKEND_LOGIC_COMPLETE.md` — All code & specs (NEW)
7. `IMPLEMENTATION_COMPLETE.md` — This file (NEW)
8. `data/routes.json` — 4 Chennai bus routes
9. `data/safe_points.json` — 5 verified safe points
10. `agents/intake_agent_prompt.md` — Claude system prompt
11. `agents/route_and_sakhi_lookup.py` — Core Python logic (tested ✅)
12. `n8n/WORKFLOW_BLUEPRINT.md` — 8-node workflow spec

✅ **To Create (Phase 2+):**
- `safepath_backend.py` — Flask backend (code above)
- `dashboard.html` — Web dashboard (code in BACKEND_LOGIC_COMPLETE.md)
- `.env` — Your credentials (template above)
- `.env` added to `.gitignore` (don't commit!)

---

## Success Criteria (Judges will see this)

✅ **By end of Day 1:**
- Send SMS → Get free bus route + safe point back (< 5 sec)
- Works on basic phone (ASCII only, no app, no internet needed)
- Reply includes bus number, frequency, safe waiting point

✅ **By end of Day 2:**
- Send "START" → Journey Watch timer runs
- Send "REACHED" → Confirmed safe arrival
- "HELP" → Alert sent to trusted contacts

✅ **By end of Day 3:**
- Dashboard shows: total requests, top routes, peak times
- Data is real (routes from Chennai MTC, safe points verified)
- Narrative is clear: SDG 5 = removing barriers to safe mobility

---

## Troubleshooting

### SMS not being received by n8n
- Check Twilio webhook URL is correct in Phone Settings
- Test webhook URL manually with curl: `curl -X POST https://your-webhook-url -d '{"From": "+1234", "Body": "test"}'`

### Claude API returning errors
- Check API key is correct in .env
- Check request format matches Claude API docs
- Try simpler SMS first: "route A to B"

### n8n nodes failing
- Check error message in node (red indicator)
- Test each node independently with sample data
- Verify all credentials are correct

### Route matching wrong
- Test locally first: `python agents/route_and_sakhi_lookup.py`
- Check routes.json has correct stop names
- Increase/decrease fuzzy match threshold in Python code

---

## Next Steps for You

1. **Read this file again** (15 min) — Understand the complete picture
2. **Get the 3 API keys** (35 min) — Twilio, Claude, n8n
3. **Create .env file** (5 min)
4. **Run local tests** (30 min) — Python scripts
5. **Build n8n workflow** (4 hours) — Follow WORKFLOW_BLUEPRINT.md
6. **Go live** (1 hour) — Test with real SMS
7. **Add Journey Watch** (4-6 hours, parallel)
8. **Add Dashboard** (3-4 hours, parallel)

**Total for full Phase 1+2+3: 12-16 hours with 2 people, working in parallel.**

---

## Files to Share with Team

| File | Who | Purpose |
|------|-----|---------|
| SafePath_Refocused_Brief_v2.pdf | Everyone | Understand the vision |
| README.md | Everyone | Project navigation |
| API_KEYS_AND_SETUP.md | Tech Lead | Know what to get |
| IMPLEMENTATION_COMPLETE.md | Devs | Know what to build |
| BACKEND_LOGIC_COMPLETE.md | Backend dev | Code specs |
| WORKFLOW_BLUEPRINT.md | n8n dev | Workflow nodes |
| agents/intake_agent_prompt.md | Claude dev | System prompt |

---

**You're ready. Good luck! 🚌**
