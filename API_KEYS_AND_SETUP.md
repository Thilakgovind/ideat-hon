# SafePath: API Keys & Setup Requirements

**Last Updated:** 2024-10-23  
**Status:** Phase 1 (SMS Core) Ready for Implementation

---

## API Keys: What You Actually Need vs. What You Listed

### ✅ REQUIRED for Phase 1 (SMS Core - 6-8 hours)

| Key | Purpose | Phase | Get It | Notes |
|-----|---------|-------|--------|-------|
| **Twilio Account SID + Auth Token** | SMS gateway (send/receive) | 1 | [https://www.twilio.com/try-twilio](https://www.twilio.com/try-twilio) | Trial account, verified phone only |
| **Twilio Trial Phone Number** | Your SMS endpoint number | 1 | Generated in Twilio console | e.g., +1 (555) 123-4567 |
| **Claude API Key** | Intake Agent (SMS parsing) | 1 | [https://console.anthropic.com/](https://console.anthropic.com/) | Get from Anthropic dashboard |
| **n8n Instance** | Orchestration (workflow engine) | 1 | [https://n8n.io](https://n8n.io) (cloud) or `npm install -g n8n` (local) | Cloud version = no setup; local = 1 hour |
| **n8n Webhook URL** | Generated after n8n deploy | 1 | Auto-generated | Example: `https://xxx.n8n.cloud/webhook` |

**Setup Time: ~1 hour**

---

### 🔄 OPTIONAL for Phase 2+ (Journey Watch, Dashboard, Stretch Goals)

| Key | Purpose | Phase | Priority | Notes |
|-----|---------|-------|----------|-------|
| **Firebase or Supabase Project** | Persistent database (after 72h) | 2-3 | Medium | JSON works for ideathon; upgrade post-event |
| **Sarvam API Key** | Tamil voice agent (stretch goal) | 3 | Low | Day 3 only if time; SMS core works without it |

**Setup Time: 2-4 hours (not needed for Phase 1)**

---

### ❌ NOT NEEDED (Not in SafePath Scope)

| Key | Why Not | Alternative |
|-----|---------|-------------|
| **Gemini API key** | SafePath uses Claude (better for Tamil). Gemini is backup only for token budgeting post-launch. | Not needed for Phase 1 |
| **Razorpay key** | No payments in ideathon scope. Women contact info, not payment processing. | Out of scope |

---

## Setup Checklist

### ✅ Before You Start
- [ ] You have a Twilio trial account (get one in 5 min at https://www.twilio.com/try-twilio)
- [ ] You have a Claude API key from https://console.anthropic.com/
- [ ] You have npm installed (for local n8n) OR will use n8n cloud (https://n8n.io)

### Step 1: Twilio (15 min)
```
1. Sign up at https://www.twilio.com/try-twilio
2. Verify your phone (you'll use this for testing)
3. Get Account SID and Auth Token from console
4. Get your trial phone number (e.g., +1234567890)
5. Save to .env:
   TWILIO_ACCOUNT_SID=your_sid
   TWILIO_AUTH_TOKEN=your_token
   TWILIO_PHONE=+1234567890
```

### Step 2: Claude API (5 min)
```
1. Go to https://console.anthropic.com/
2. Create API key
3. Save to .env:
   CLAUDE_API_KEY=your_key
```

### Step 3: n8n (30 min - Cloud) or (1 hour - Local)
**Option A: Cloud (Recommended for ideathon)**
```
1. Go to https://n8n.io
2. Sign up for free cloud plan
3. Create a new workflow
4. Copy your public webhook URL
5. Save to .env:
   N8N_WEBHOOK_URL=https://your-instance.n8n.cloud/webhook
```

**Option B: Local Installation**
```
bash
npm install -g n8n
n8n start
# Visit http://localhost:5678
# Public URL will show in n8n console
```

### Step 4: Test Basic Setup (30 min)
```bash
# Test route lookup (should pass)
python agents/route_and_sakhi_lookup.py

# Test Claude API
python test_intake.py  # (create this from SETUP_GUIDE.md)

# Test n8n webhook (follow WORKFLOW_BLUEPRINT.md)
```

---

## .env File Template

Create `.env` in project root (DO NOT COMMIT):

```
# Twilio Credentials
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE=+1234567890

# Claude API
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx

# n8n
N8N_WEBHOOK_URL=https://xxx.n8n.cloud/webhook
N8N_API_KEY=optional_if_local  # Only needed if you're calling n8n API

# Firebase / Supabase (Phase 2, optional)
# FIREBASE_PROJECT_ID=your_project
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_KEY=your_anon_key

# Sarvam (Stretch goal, optional)
# SARVAM_API_KEY=your_sarvam_key
```

---

## Cost Estimate (72-hour Ideathon)

| Service | Free Tier | Cost for Ideathon |
|---------|-----------|-------------------|
| Twilio | 50 SMS | $0 (verified phone only) |
| Claude API | None, but credits | ~$5-20 (500 requests @ ~0.01 each) |
| n8n Cloud | 0 (cloud = paid) | $0 (Starter = $20/mo, can demo on free) |
| n8n Local | ∞ (open source) | $0 |
| Firebase | 50k ops/month | $0 (free tier) |

**Recommended:** Use Twilio trial + Claude API + n8n cloud = ~$0-20 for 72h

---

## What You Don't Have Yet (What to Get)

Based on the above:

- [ ] **Twilio:** Phone number + SID/Token (15 min)
- [ ] **Claude API:** Key from Anthropic (5 min)
- [ ] **n8n:** Cloud instance with webhook URL (15 min)

**All three together = 35 minutes to full SMS core readiness**

---

## Next Steps

1. **Get the three keys above** (35 min)
2. **Follow SETUP_GUIDE.md Part 1-4** (workflow build, 4 hours)
3. **Test with sample SMS** (see SETUP_GUIDE.md Part 5)

**Once SMS core works**, you can add:
- Journey Watch (4-6 hours)
- Dashboard (3-4 hours)
- Sarvam voice (stretch, 2-3 hours)

---

**Ready to proceed? Get those 3 keys first.** Once you do, the SETUP_GUIDE.md has you covered for the next 6-8 hours.
