# SafePath V1 · AVAL (அவள்)

Women's travel companion for Chennai (SDG 5). Finds the safest way to travel
(bus / metro / train / auto), safe places to wait, and keeps a trusted circle
informed. **All data is sample data for the demo.**

## Run it (Windows, from the repo root)

**1. Backend (FastAPI, port 8000)**

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r backend/requirements.txt
.venv/Scripts/python -m uvicorn backend.app:app --port 8000
```

Check http://localhost:8000/health (shows which services are real vs mock) and http://localhost:8000/docs.

**2. Frontend (React + Vite, port 5173)** — in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 (Vite proxies `/api` to the backend).

**3. Tests**

```bash
.venv/Scripts/python -m pytest backend/tests -q
```

**Keys are optional.** Copy `.env.example` to `.env` and fill in what you have.
Every service without a key runs as a mock (demo mode); see `backend/README.md`.

## Demo paths
- Login → Home → Safe way home → Walk main road → Live trip → SOS (hold 2 s)
- AVAL chat ("Nungambakkam, 8am, with my daughter") → Metro instead → Choose ride → Payment → Ticket

Screenshots: `docs/screenshots/`.

## Layout
```
backend/   FastAPI agents (intake, route, safety, places, circle, pay, voice, sms), guardrails, tests
frontend/  React + Vite + Tailwind + shadcn/ui, 17 screens
data/      sample routes, metro, trains, places, walk paths, circle (all "source": "sample")
design/    design handoff (screens, AVAL art, briefs)
agents/    earlier prototype prompt + lookup script
n8n/       workflow blueprint
docs/      screenshots
```

---

# Earlier planning notes (pre-V1)

# SafePath: Women's Transport Intelligence System

**Ideathon: SDG 5 (Gender Equality)**

A real-time, SMS-first mobility assistant for women in Tamil Nadu using a 4-agent system (Intake, Free-Bus Route, Journey Watch, Sakhi Network) orchestrated by n8n.

---

## Project Structure

```
murdermurugaveni/
├── SafePath_Refocused_Brief_v2.pdf       ← START HERE (read first)
├── SETUP_GUIDE.md                         ← Build instructions (step-by-step)
├── README.md                              ← This file
│
├── data/
│   ├── routes.json                        ← 4 bus routes (Chennai MTC)
│   └── safe_points.json                   ← 5 verified safe waiting points
│
├── agents/
│   ├── intake_agent_prompt.md             ← Claude system prompt (SMS parsing)
│   └── route_and_sakhi_lookup.py          ← Route matching logic (tested ✅)
│
└── n8n/
    ├── WORKFLOW_BLUEPRINT.md              ← Detailed node-by-node spec
    └── [coming] JOURNEY_WATCH_BLUEPRINT.md
```

---

## Quick Start (for the team)

### Day 1: Research & Setup (6-8 hours)
- [ ] Read `SafePath_Refocused_Brief_v2.pdf` (understand the vision & scope)
- [ ] Set up Twilio trial account (30 min)
- [ ] Set up Claude API key (15 min)
- [ ] Test route lookup locally: `python agents/route_and_sakhi_lookup.py` (should pass)

### Day 1-2: Build Core SMS Flow (6-8 hours)
- [ ] Follow `SETUP_GUIDE.md` Part 3 & 4
- [ ] Build n8n workflow (7 nodes, follow blueprint)
- [ ] Connect Twilio → n8n webhook
- [ ] Test with 5 sample SMS (route requests, START, REACHED, HELP)

### Success: SMS Core is Live ✅
Send SMS → Get free bus route + safe point back in < 5 seconds

### Day 2-3: Add Journey Watch (4-6 hours)
- [ ] Build scheduled workflow (check-in SMS at ETA + timers)
- [ ] Test with START / REACHED / escalation

### Day 3: Polish & Demo (4-6 hours)
- [ ] Build policy dashboard (anon request log)
- [ ] Record demo video (Priya's journey)
- [ ] Slides + narrative

---

## The 4 Agents (What Each Does)

| Agent | Job | Input → Output |
|-------|-----|--------|
| **Intake** | Parse messy SMS | "t nagar to nungambakkam 8" → `{intent, from, to, time, language}` |
| **Free-Bus Route** | Find free buses first | from/to → List of free buses, frequencies, next arrival |
| **Journey Watch** | Track trip, alert family | START → timer → check-in at ETA+10m → escalate at ETA+25m |
| **Sakhi Network** | Find safe waiting points | stop_code → List of SHG/women-run shops near stop |

---

## How It Works: Example SMS Journey

```
User:   "T Nagar to Nungambakkam 8 mani paapa"
        ↓ (SMS arrives at Twilio)
        
n8n:    [Parse SMS]
        ↓
        [Intake Agent: Claude parses intent]
        → intent=route_request, from="T. Nagar", to="Nungambakkam", 
          time="8:00", has_child=true
        ↓
        [Route Lookup: Python logic]
        → 21G FREE bus, 15-min frequency
        ↓
        [Sakhi Lookup: Find safe point at stop]
        → Lakshmi Tea Stall (SHG) opposite main stop
        ↓
        [Format Reply: Build SMS]
        ↓
        [Send SMS via Twilio]
        
User:   "BUS 21G [FREE]
         T. Nagar → Nungambakkam
         Every 15 min
         Wait at: Lakshmi Tea Stall (SHG)
         
         Reply START when you board..."
```

---

## Key Design Decisions (Why This Works for SDG 5)

1. **Button phone first** ✓
   - No smartphone, no internet, no app needed
   - SMS works on Rs. 1,000 phones
   - Includes the most excluded women

2. **Free bus as the anchor** ✓
   - Tamil Nadu's Vidiyal Payanam scheme already exists
   - Most women don't know which buses are free
   - Saves money, enables economic opportunity (SDG 5.5)

3. **SHGs as the safety network** ✓
   - Self-Help Groups are an existing nationwide network
   - Women-run stalls & shops = real economic participation
   - Verified safe points > "danger scores" (no stigma)

4. **Family loop without surveillance** ✓
   - She starts Journey Watch manually (not always-on tracking)
   - She can DELETE all data anytime
   - Addresses risks of controlling relatives

5. **Policy dashboard (anonymous)** ✓
   - Aggregate requests without names/phones
   - Shows transport dept where women's needs aren't met
   - System-level impact, not just one-off help

---

## What We're NOT Building (Deliberately Cut)

- ❌ AI that "learns" behavior in 72 hours (faked learning loses credibility)
- ❌ Location tracking / GPS (adds risk, unnecessary for SMS-based proof)
- ❌ 7 agents (too many for 72h; 4 agents execute better)
- ❌ Full survey of 100 women (realistic: 20-40 quick interviews)
- ❌ 4 channels at once (SMS first; WhatsApp is stretch goal)

Why? **Judges value honest scope + solid execution over feature bloat.**

---

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Orchestration | n8n | Orchestrates SMS → agents → reply |
| LLM | Claude API | Best for Tamil/Tanglish understanding |
| Route logic | Python function | Deterministic, fast, no hallucination |
| SMS Gateway | Twilio | Simple, trial-friendly, good docs |
| Data | JSON files (Supabase later) | Fast for 72-hour sprint |
| Dashboard | Simple web page | Read-only analytics, minimal code |

---

## Next Steps (In Order)

1. **[NOW]** Read this README + the brief
2. **[NOW]** Test route lookup locally (should pass)
3. **[Next 6-8h]** Set up Twilio + n8n + Claude, build SMS core
4. **[When SMS works]** Add Journey Watch (scheduler + escalation)
5. **[Day 3]** Build dashboard, record demo, finalize slides

---

## Common Questions

**Q: What if Twilio trial doesn't work?**
A: Use an Android phone as SMS gateway (slower but works for demo). Or use the public n8n test numbers.

**Q: What if Claude misparses the SMS?**
A: Fallback to a generic "I didn't understand" reply + log for review. The system degrades gracefully.

**Q: Is this real or just a prototype?**
A: Working prototype with real SMS, real bus routes (mock safe points). No hallucinated data. Judges can test it themselves.

**Q: Can this scale beyond 72 hours?**
A: Yes. After the ideathon, replace JSON with Supabase, add Sarvam voice, add real SHG verification. The architecture doesn't change.

---

## Success Criteria (Remember These for the Pitch)

✅ **At the demo, judges should see:**
1. A woman texts a question in Tamil on a basic phone
2. Within 5 seconds, she gets a **free bus** recommendation
3. The system also suggests a **safe waiting point** run by an SHG
4. She can **start a trip** (Journey Watch) and will be checked on
5. The request (anonymized) feeds into a **policy dashboard**
6. Narrative is clear: **"SDG 5 = removing barriers. This system does that."**

**Not impressed by:** 7 agents, fancy architecture, "AI learns over time"
**Impressed by:** Button phone works, free bus is smart, SHGs are the network

---

## Files to Read in Order

1. `SafePath_Refocused_Brief_v2.pdf` (5 min) — the full story
2. `SETUP_GUIDE.md` (15 min) — step-by-step build instructions
3. `n8n/WORKFLOW_BLUEPRINT.md` (30 min) — detailed technical spec
4. `agents/intake_agent_prompt.md` (10 min) — what Claude does
5. `data/routes.json` + `data/safe_points.json` (skim, understand structure)
6. `agents/route_and_sakhi_lookup.py` (understand the logic, but don't modify unless needed)

---

## Contact & Questions

- All code is here in this folder
- Logs and test runs go in `/logs`
- Data backups go in `/backups`
- Keep `.env` local (never commit credentials)

**Good luck! You've got this.** 🚌✨
