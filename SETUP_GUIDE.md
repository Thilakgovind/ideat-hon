# SafePath SMS Core: Setup & Build Guide

## Status: ✅ READY TO BUILD

You have:
- ✅ Route & safe point mock data (routes.json, safe_points.json)
- ✅ Route lookup logic (working Python script tested)
- ✅ Intake agent prompt (ready for Claude API)
- ✅ n8n workflow blueprint (detailed node specs)
- ✅ Sample SMS reply formatting

**Estimated build time:** 6-8 hours for a working SMS flow (with 2 people)

---

## Part 1: Set Up Twilio (30 min)

### 1.1 Create Twilio Trial Account
1. Go to https://www.twilio.com/try-twilio
2. Sign up with email + phone verification
3. **Get your Twilio credentials:**
   - Account SID (in console)
   - Auth Token (in console)
   - Trial phone number (e.g., +1234567890)

**Note:** Trial accounts can send/receive SMS from verified numbers only. For testing, you can:
- Add your personal phone number as a verified number
- Or use an Android phone as a mock SMS gateway (see stretch goal below)

### 1.2 Save Credentials Locally
Create a `.env` file in your project (DO NOT commit to git):
```
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE=+1234567890

CLAUDE_API_KEY=your_claude_pro_api_key
```

---

## Part 2: Set Up Claude API (15 min)

### 2.1 Get Claude API Key
1. Go to https://console.anthropic.com/
2. Create an API key (if you haven't already)
3. Copy the key into `.env` above

### 2.2 Test the Intake Agent Locally
```bash
cd C:\Users\THILAK GOVIND\OneDrive\Desktop\murdermurugaveni

# Install dependencies (if needed)
pip install requests

# Create a test script
```

Save as `test_intake.py`:
```python
import json
import requests
from pathlib import Path
import os

API_KEY = os.getenv("CLAUDE_API_KEY")

# Read the Intake agent prompt
with open("agents/intake_agent_prompt.md") as f:
    system_prompt = f.read()

# Test SMS
test_sms = "T Nagar to Nungambakkam 8 mani, paapa kooda"

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
        "messages": [{"role": "user", "content": f"Parse this SMS:\n\n{test_sms}"}],
    }
)

result = response.json()
print(json.dumps(result, indent=2))

# Extract and parse the JSON response
if "content" in result and len(result["content"]) > 0:
    intent_json = result["content"][0]["text"]
    print("\nParsed intent:")
    print(json.dumps(json.loads(intent_json), indent=2))
```

Run it:
```bash
python test_intake.py
```

You should see a JSON response with `intent`, `from`, `to`, `time`, `language`, etc.

---

## Part 3: Set Up n8n (1 hour)

### 3.1 Install n8n
```bash
npm install -g n8n
n8n start
```

Or use the **free cloud version** at https://n8n.io/ (no installation needed).

### 3.2 Create the Webhook-to-SMS Workflow
Follow the **WORKFLOW_BLUEPRINT.md** step-by-step:

1. **Webhook Trigger**
   - Listen on `/webhook`
   - Extract Twilio payload

2. **Parse SMS** (Set node)
   - Extract phone, text, timestamp

3. **Call Claude Intake Agent** (HTTP Request)
   - POST to `https://api.anthropic.com/v1/messages`
   - Use system prompt from `agents/intake_agent_prompt.md`
   - Parse the JSON response

4. **Route Lookup** (Code node or Function)
   - Use the logic from `route_and_sakhi_lookup.py`
   - Load routes.json, match from/to, return best 2 routes

5. **Sakhi Network Lookup** (Code node)
   - Load safe_points.json, find points near the boarding stop

6. **Format Reply** (Set node)
   - Build a human-readable SMS message

7. **Send SMS Reply** (HTTP Request to Twilio)
   - POST to Twilio API to send the reply

### 3.3 Get the n8n Webhook URL
- Once deployed, copy the Public URL from n8n
- It will look like: `https://xxx.n8n.cloud/webhook`

---

## Part 4: Connect Twilio → n8n (15 min)

### 4.1 Configure Twilio Webhook
1. Go to Twilio Console → Phone Numbers → Manage Numbers
2. Select your trial number
3. Under **Messaging**, find **A message comes in**
4. Set the webhook URL to: `https://your-n8n-instance.com/webhook`
5. Choose **HTTP POST**
6. Save

### 4.2 Test the Full Flow
1. Send a test SMS to your Twilio number from your phone:
   ```
   "T Nagar to Nungambakkam 8 mani"
   ```

2. You should receive back within 5 seconds:
   ```
   BUS 21G [FREE]
   T. Nagar Depot -> Nungambakkam
   Every 15 min

   Wait at: Lakshmi Tea Stall (SHG)
   (Opposite the main stop, under the lamp)

   Reply START when you board.
   Reply REACHED when you arrive.
   Reply HELP anytime.
   ```

3. If it fails, check:
   - n8n workflow logs (any errors?)
   - Twilio logs (was SMS received?)
   - Claude API response (was intent parsed?)

---

## Part 5: Test Cases (30 min)

Try these SMS and verify the replies:

| SMS | Expected Intent | Expected Reply |
|-----|---|---|
| `"T Nagar to Nungambakkam 8 mani"` | route_request | 21G bus info + safe point |
| `"START"` | start_trip | "Journey Watch is ON" |
| `"REACHED"` | reached | "Safe reach confirmed" |
| `"HELP"` | help | "Help alert sent to contacts" |
| `"nungambakkam anna nagar evening"` | route_request | Best route for that pair |

---

## Part 6: Next Milestone: Journey Watch (4-6 hours)

Once SMS core is working, add the **Journey Watch scheduler**:

1. **Separate n8n workflow** triggered by `START` SMS
2. Store ETA = current time + expected travel time
3. Set a timer (using n8n Delay node)
4. At ETA + 10 min: send check-in SMS
5. At ETA + 25 min: send alert to trusted contacts

This is a **scheduled workflow**, not a webhook. See `n8n/JOURNEY_WATCH_BLUEPRINT.md` (coming next).

---

## Troubleshooting

### n8n nodes keep failing
- **Check the error log** in the n8n UI (bottom of node)
- **Test each node independently** (use Test Data or Webhook test)
- **Verify API credentials** are correct (CLAUDE_API_KEY, TWILIO tokens)

### Twilio SMS not coming in
- **Is the phone number verified?** Add it in Twilio Console
- **Is the webhook URL correct?** Copy it exactly from n8n
- **Check Twilio logs** for delivery status

### Claude is returning unparseable JSON
- **Check the system prompt** is complete
- **Try a simpler SMS** first (e.g., "route A to B")
- **Check token count** (shouldn't exceed 500)

### Routes not matching
- **Test locally first:** `python agents/route_and_sakhi_lookup.py`
- **Are stop names spelled correctly** in routes.json?
- **Try a known route:** "T. Nagar to Nungambakkam"

---

## Files Reference

| File | Purpose |
|------|---------|
| `data/routes.json` | Bus routes & stops (Chennai MTC) |
| `data/safe_points.json` | Verified safe waiting points (mock) |
| `agents/intake_agent_prompt.md` | System prompt for Claude (SMS parsing) |
| `agents/route_and_sakhi_lookup.py` | Route matching & safe point lookup (tested) |
| `n8n/WORKFLOW_BLUEPRINT.md` | Detailed n8n node specs |

---

## Success Criteria for Part 1

✅ When complete, you should be able to:
1. Send an SMS to a Twilio number
2. Receive back a route + safe point in < 5 seconds
3. n8n workflow logs show no errors
4. Claude API is being called (verify in logs)

Once this works, you're ready to add Journey Watch, the policy dashboard, and multi-language support.

---

**Time estimate: 4-6 hours for 2 people to get SMS core live.**

Ready to start? Questions?
