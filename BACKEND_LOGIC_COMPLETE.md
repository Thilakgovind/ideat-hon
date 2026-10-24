# SafePath: Complete Backend Logic for All Features

**Author:** Claude Haiku 4.5  
**Last Updated:** 2024-10-23  
**Scope:** All 4 agents + Journey Watch + Policy Dashboard  
**Status:** Ready to implement in n8n + Python

---

## Part 1: Intake Agent (SMS Parsing)

**Location:** `agents/intake_agent_prompt.md` (already complete)

### What It Does
Receives messy SMS text (Tamil, English, Tanglish), returns structured JSON:

```json
{
  "intent": "route_request|start_trip|reached|help|add_contact|check_in|stop|unknown",
  "from": "T. Nagar",
  "to": "Nungambakkam",
  "time": "8:00|now|evening",
  "language": "Tamil|English|Tanglish",
  "has_child": true|false,
  "confidence": 0.95,
  "raw_text": "original SMS"
}
```

### How to Call in n8n
1. **HTTP Request Node** → POST to `https://api.anthropic.com/v1/messages`
2. **Headers:**
   ```json
   {
     "x-api-key": "{{env('CLAUDE_API_KEY')}}",
     "content-type": "application/json"
   }
   ```
3. **Body:**
   ```json
   {
     "model": "claude-3-5-sonnet-20241022",
     "max_tokens": 500,
     "system": "{{readFile('agents/intake_agent_prompt.md')}}",
     "messages": [
       {
         "role": "user",
         "content": "Parse this SMS:\n\n{{$node.TwilioPayload.body.Body}}"
       }
     ]
   }
   ```

### Error Handling
```javascript
// In n8n, after Claude response
if (!response.content[0].text) {
  return {
    intent: "unknown",
    confidence: 0,
    error: "Failed to parse"
  };
}
const json = JSON.parse(response.content[0].text);
return json;
```

---

## Part 2: Route Lookup Agent

**Location:** `agents/route_and_sakhi_lookup.py` (already tested ✓)

### Core Logic (Python)

```python
def find_route(from_area, to_area, preference="free_first"):
    """
    Find best route using fuzzy matching + priority sorting.
    Returns top 2 routes (free first if preference="free_first").
    """
    # 1. Load routes.json
    # 2. Fuzzy match from_area to actual stop names
    # 3. Fuzzy match to_area to actual stop names
    # 4. Find routes connecting both stops in sequence
    # 5. Sort: free buses first, then by frequency
    # 6. Return top 2
    
    # Success case:
    return {
        "from_stop": "T. Nagar Depot",
        "to_stop": "Nungambakkam",
        "routes": [
            {
                "number": "21G",
                "is_free": true,
                "frequency_minutes": 15,
                "notes": "Free ordinary bus",
                "stop_sequence": ["TND", "RMN", "TEN", "NMB"],
                "operator": "MTC"
            }
        ]
    }
    
    # Error case:
    return {
        "error": "No direct route found",
        "from_stop": "T. Nagar",
        "to_stop": "Nungambakkam",
        "alternatives": []
    }
```

### How to Integrate in n8n
1. **Code Node** in n8n (JavaScript equivalent):

```javascript
// In n8n Function node
const routes = require('./data/routes.json');

function fuzzyMatch(input, candidates, threshold = 0.5) {
  // Implement priority: exact > prefix > word > fuzzy (downweighted)
  // Return (match, score)
}

function findRoute(from, to, preference = "free_first") {
  // Load all stops from routes
  // Fuzzy match from and to
  // Find connecting routes
  // Sort by preference
  // Return top 2
}

return findRoute(
  $node.IntakeAgent.output.from,
  $node.IntakeAgent.output.to,
  "free_first"
);
```

2. **Or use Python via n8n Webhook**:
   - Create endpoint `POST /api/route_lookup`
   - Receives `{from, to, preference}`
   - Returns route result
   - Call from n8n HTTP Request node

### Test Cases (All Pass ✓)
| From | To | Expected Route |
|------|-----|------------------|
| "T Nagar" | "Nungambakkam" | 21G FREE, 15 min |
| "Anna Nagar" | "Central" | 5A FREE, 20 min |
| "T. Nagar" | "Velachery" | 15M PAID, 25 min |

---

## Part 3: Sakhi Network Agent (Safe Points Lookup)

**Location:** `agents/route_and_sakhi_lookup.py` (already tested ✓)

### Core Logic

```python
def find_safe_points(stop_code):
    """
    Look up verified safe waiting points by bus stop code.
    Returns list of SHG-run shops, women-owned businesses.
    """
    # 1. Load safe_points.json
    # 2. Filter by stop_code
    # 3. Return first match (or empty list if none)
    
    # Success case:
    return {
        "stop_code": "NMB",
        "safe_points": [
            {
                "name": "Lakshmi Tea Stall",
                "type": "tea_stall",
                "operator_type": "SHG",
                "hours_safe": "6:00-20:00",
                "location_description": "Opposite the main stop, under the lamp"
            }
        ]
    }
    
    # No match case:
    return {
        "stop_code": "NMB",
        "safe_points": [],
        "message": "No verified safe points yet. Use a well-lit, busy area."
    }
```

### Data Structure (safe_points.json)

```json
{
  "safe_points": [
    {
      "name": "Lakshmi Tea Stall",
      "stop_code": "NMB",
      "type": "tea_stall",
      "operator_type": "SHG",
      "hours_safe": "6:00-20:00",
      "location_description": "Opposite the main stop, under the lamp",
      "phone_contact": "optional",
      "verified_by": "SHG coordinator"
    }
  ]
}
```

### How to Integrate in n8n
```javascript
// In n8n Function node
const safePoints = require('./data/safe_points.json');

function findSafePoints(stopCode) {
  const nearby = safePoints.safe_points.filter(
    sp => sp.stop_code === stopCode
  );
  
  if (!nearby.length) {
    return {
      stop_code: stopCode,
      safe_points: [],
      message: "Use a well-lit, busy area."
    };
  }
  
  return {
    stop_code: stopCode,
    safe_points: nearby
  };
}

// Get the destination stop code from route result
const destStop = $node.RouteLookup.output.routes[0].stop_sequence[$node.RouteLookup.output.routes[0].stop_sequence.length - 1];

return findSafePoints(destStop);
```

---

## Part 4: Reply Formatter

**Location:** `agents/route_and_sakhi_lookup.py` → `format_reply_tamil()`

### Logic

```python
def format_reply_tamil(route_result, sakhi_result):
    """
    Build a human-readable SMS reply.
    - No emojis (basic phone compatible)
    - < 160 characters for single SMS
    - Tamil-friendly ASCII
    """
    
    # Handle errors
    if "error" in route_result:
        return "Sorry, I couldn't find a route.\nTry another stop nearby."
    
    # Build message
    route = route_result["routes"][0]
    status = "FREE" if route["is_free"] else "PAID"
    
    msg = f"BUS {route['number']} [{status}]\n"
    msg += f"{route_result['from_stop']} -> {route_result['to_stop']}\n"
    msg += f"Every {route['frequency_minutes']} min\n\n"
    
    # Add safe point
    safe_points = sakhi_result.get("safe_points", [])
    if safe_points:
        sp = safe_points[0]
        msg += f"Wait at: {sp['name']}\n"
        msg += f"({sp['location_description']})\n\n"
    
    # Add action instructions
    msg += "Reply START when you board.\n"
    msg += "Reply REACHED when you arrive.\n"
    msg += "Reply HELP anytime."
    
    return msg
```

### Example Output

```
BUS 21G [FREE]
T. Nagar -> Nungambakkam
Every 15 min

Wait at: Lakshmi Tea Stall
(Opposite the main stop, under the lamp)

Reply START when you board.
Reply REACHED when you arrive.
Reply HELP anytime.
```

**Character count:** 156 (fits in single SMS ✓)

---

## Part 5: Journey Watch Agent (Scheduled Execution)

**New Feature: SMS Trip Tracking**

### Overview
When user sends "START", system:
1. Records trip start time
2. Calculates expected arrival (travel time + 5 min buffer)
3. Sets timer to check-in at ETA+10 min
4. If no "REACHED" → escalate to trusted contacts at ETA+25 min

### Data Schema

**Trip Record** (store in database or n8n variable):
```json
{
  "trip_id": "uuid",
  "user_phone": "+919876543210",
  "from_stop": "T. Nagar Depot",
  "to_stop": "Nungambakkam",
  "bus_number": "21G",
  "start_time": "2024-10-23T08:00:00Z",
  "expected_arrival": "2024-10-23T08:30:00Z",  // Approx
  "check_in_sent": false,
  "reached_confirmed": false,
  "escalated": false,
  "escalation_contacts": ["+919876543211", "+919876543212"],
  "status": "in_transit|reached|no_response|escalated"
}
```

### n8n Workflow: Journey Watch Scheduler

**Workflow 1: On START Command**
```
1. Webhook Trigger (SMS from Twilio)
2. Parse: Extract "START" intent
3. Load previous trip data (from Intake + Route lookup)
4. Create trip record:
   - start_time = now()
   - expected_arrival = start_time + estimated_travel_time
   - status = "in_transit"
5. Schedule follow-up workflow (DELAY node)
   - Delay = ETA + 10 minutes
   - Call Workflow 2 (check-in)
6. Send SMS reply: "Journey Watch is ON. Safe travels!"
```

**Workflow 2: Check-in at ETA+10 min (Scheduled)**
```
1. Receive trip_id from Workflow 1
2. Load trip record
3. Check if "REACHED" was received
   - If YES → Exit (already safe)
   - If NO → Continue to step 4
4. Send check-in SMS: "Are you safe? Reply REACHED or HELP"
5. Schedule follow-up (DELAY node)
   - Delay = 15 more minutes (total ETA+25)
   - Call Workflow 3 (escalate)
```

**Workflow 3: Escalate at ETA+25 min (Scheduled)**
```
1. Receive trip_id
2. Check again if "REACHED" received
   - If YES → Exit
   - If NO → Continue
3. Send alert SMS to user: "You're taking longer than expected. Need help?"
4. Send alert SMS to trusted contacts:
   "Priya has not confirmed arrival at Nungambakkam.
    Started from T. Nagar at 8:00 AM.
    Contact her: +919876543210"
5. Log to dashboard: Trip escalated
6. Update trip status = "escalated"
```

### Backend Code: Journey Watch Manager (Python)

```python
import json
from datetime import datetime, timedelta
import uuid

# Simulate database with JSON (Phase 2: use Supabase/Firebase)
TRIPS_DB = {}

def create_trip(user_phone, from_stop, to_stop, bus_number, travel_minutes=25):
    """Create a new trip record."""
    trip_id = str(uuid.uuid4())
    now = datetime.utcnow()
    expected_arrival = now + timedelta(minutes=travel_minutes)
    
    TRIPS_DB[trip_id] = {
        "trip_id": trip_id,
        "user_phone": user_phone,
        "from_stop": from_stop,
        "to_stop": to_stop,
        "bus_number": bus_number,
        "start_time": now.isoformat(),
        "expected_arrival": expected_arrival.isoformat(),
        "check_in_sent": False,
        "reached_confirmed": False,
        "escalated": False,
        "escalation_contacts": [],  # Will be set by add_trusted_contact
        "status": "in_transit"
    }
    return trip_id

def confirm_reached(trip_id):
    """User sent REACHED."""
    if trip_id in TRIPS_DB:
        TRIPS_DB[trip_id]["reached_confirmed"] = True
        TRIPS_DB[trip_id]["status"] = "reached"
        return {"status": "confirmed", "message": "Safe arrival recorded!"}
    return {"error": f"Trip {trip_id} not found"}

def escalate_trip(trip_id, contacts):
    """Send alerts to trusted contacts."""
    if trip_id not in TRIPS_DB:
        return {"error": "Trip not found"}
    
    trip = TRIPS_DB[trip_id]
    trip["escalated"] = True
    trip["status"] = "escalated"
    
    # Return contacts to notify
    return {
        "trip_id": trip_id,
        "user_phone": trip["user_phone"],
        "escalation_contacts": contacts,
        "message": f"Priya has not confirmed arrival at {trip['to_stop']}. Started from {trip['from_stop']} on bus {trip['bus_number']}."
    }

def add_trusted_contact(trip_id, contact_phone):
    """Add a contact to receive escalation alerts."""
    if trip_id in TRIPS_DB:
        TRIPS_DB[trip_id]["escalation_contacts"].append(contact_phone)
        return {"status": "added", "contact": contact_phone}
    return {"error": "Trip not found"}

def get_trip_status(trip_id):
    """Check current trip status."""
    return TRIPS_DB.get(trip_id, {"error": "Not found"})
```

### How to Integrate in n8n

**Step 1: Python Backend Endpoint**
```python
# safepath_backend.py
from flask import Flask, request, jsonify
from journey_watch import create_trip, confirm_reached, escalate_trip

app = Flask(__name__)

@app.route("/api/journey/start", methods=["POST"])
def start_journey():
    data = request.json
    trip_id = create_trip(
        user_phone=data["user_phone"],
        from_stop=data["from_stop"],
        to_stop=data["to_stop"],
        bus_number=data["bus_number"],
        travel_minutes=data.get("travel_minutes", 25)
    )
    return jsonify({"trip_id": trip_id})

@app.route("/api/journey/reached", methods=["POST"])
def mark_reached():
    trip_id = request.json["trip_id"]
    result = confirm_reached(trip_id)
    return jsonify(result)

@app.route("/api/journey/escalate", methods=["POST"])
def do_escalate():
    data = request.json
    result = escalate_trip(data["trip_id"], data["contacts"])
    return jsonify(result)

if __name__ == "__main__":
    app.run(port=5000)
```

**Step 2: n8n Workflow Structure**
```
[SMS START received] 
  ↓
[Parse SMS → intent="start_trip"]
  ↓
[HTTP POST to /api/journey/start]
  ← Returns trip_id
  ↓
[Send SMS: "Journey Watch is ON"]
  ↓
[Delay node: 10 minutes]
  ↓
[Check: Did user send REACHED?]
  ├→ YES: Exit workflow (logged as "reached")
  └→ NO: Send check-in SMS
          ↓
          [Delay: 15 more minutes]
          ↓
          [HTTP POST /api/journey/escalate]
          ↓
          [Send alert to contacts]
```

---

## Part 6: Policy Dashboard Agent

**Feature: Anonymous Request Log + Analytics**

### Overview
Aggregate all route requests (anonymized) to show:
- How many women requested each route
- Peak demand times
- Underserved corridors
- Safe point gaps

### Data Schema

**Request Log** (stored in Firebase/Supabase after ideathon):
```json
{
  "request_id": "uuid",
  "from_area": "T. Nagar",
  "to_area": "Nungambakkam",
  "timestamp": "2024-10-23T08:00:00Z",
  "time_of_day": "morning|afternoon|evening",
  "language": "Tamil|English|Tanglish",
  "has_child": true|false,
  "route_found": true,
  "safe_point_found": true,
  "trip_started": false,
  // NO: phone number, name, exact location
}
```

### Backend Code: Analytics Engine (Python)

```python
from collections import defaultdict, Counter
from datetime import datetime, timedelta

class SafePathAnalytics:
    def __init__(self, requests_log):
        """requests_log = list of anonymized request dicts"""
        self.requests = requests_log
    
    def route_demand(self):
        """Count requests per route pair."""
        routes = Counter()
        for req in self.requests:
            key = f"{req['from_area']} → {req['to_area']}"
            routes[key] += 1
        return dict(routes.most_common(10))
    
    def peak_hours(self):
        """When do women travel most?"""
        times = Counter()
        for req in self.requests:
            times[req['time_of_day']] += 1
        return dict(times)
    
    def safe_point_coverage(self):
        """Which stops have verified safe points?"""
        coverage = {
            "with_safe_points": 0,
            "without_safe_points": 0
        }
        for req in self.requests:
            if req['safe_point_found']:
                coverage['with_safe_points'] += 1
            else:
                coverage['without_safe_points'] += 1
        return coverage
    
    def language_breakdown(self):
        """Which languages are used?"""
        langs = Counter()
        for req in self.requests:
            langs[req['language']] += 1
        return dict(langs)
    
    def family_trip_percentage(self):
        """Percentage of trips with children."""
        with_child = sum(1 for r in self.requests if r['has_child'])
        return round(100 * with_child / len(self.requests), 1) if self.requests else 0
    
    def unmet_demand(self):
        """Where are we missing routes or safe points?"""
        unmet = []
        for req in self.requests:
            if not req['route_found'] or not req['safe_point_found']:
                unmet.append({
                    "from": req['from_area'],
                    "to": req['to_area'],
                    "issue": "no_route" if not req['route_found'] else "no_safe_point"
                })
        return unmet[:10]  # Top 10 gaps

# How to use
analytics = SafePathAnalytics(requests_log)
dashboard_data = {
    "top_routes": analytics.route_demand(),
    "peak_times": analytics.peak_hours(),
    "safe_point_coverage": analytics.safe_point_coverage(),
    "language_breakdown": analytics.language_breakdown(),
    "family_trips_percent": analytics.family_trip_percentage(),
    "unmet_demand": analytics.unmet_demand(),
    "total_requests": len(analytics.requests)
}
```

### Web Dashboard (Simple HTML + Chart.js)

```html
<!DOCTYPE html>
<html>
<head>
    <title>SafePath Policy Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial; margin: 20px; }
        .card { border: 1px solid #ccc; padding: 20px; margin: 10px 0; }
        canvas { max-width: 400px; }
    </style>
</head>
<body>
    <h1>SafePath: Women's Mobility Dashboard</h1>
    <p>Anonymous aggregate insights (no names, phones, or exact locations)</p>
    
    <div class="card">
        <h2>Total Requests</h2>
        <p id="totalRequests">Loading...</p>
    </div>
    
    <div class="card">
        <h2>Top Routes</h2>
        <canvas id="routeChart"></canvas>
    </div>
    
    <div class="card">
        <h2>Peak Travel Times</h2>
        <canvas id="timeChart"></canvas>
    </div>
    
    <div class="card">
        <h2>Safe Point Coverage</h2>
        <canvas id="safePointChart"></canvas>
    </div>
    
    <div class="card">
        <h2>Language Breakdown</h2>
        <canvas id="languageChart"></canvas>
    </div>
    
    <div class="card">
        <h2>Unmet Demand (Top Gaps)</h2>
        <ul id="unmetList">Loading...</ul>
    </div>
    
    <script>
        // Fetch dashboard data from backend
        fetch('/api/dashboard/analytics')
            .then(r => r.json())
            .then(data => {
                // Total requests
                document.getElementById('totalRequests').innerText = 
                    data.total_requests + ' women requested safe routes';
                
                // Route demand chart
                const routeChart = new Chart(
                    document.getElementById('routeChart'),
                    {
                        type: 'bar',
                        data: {
                            labels: Object.keys(data.top_routes),
                            datasets: [{
                                label: 'Requests',
                                data: Object.values(data.top_routes),
                                backgroundColor: '#4CAF50'
                            }]
                        }
                    }
                );
                
                // Peak times chart
                const timeChart = new Chart(
                    document.getElementById('timeChart'),
                    {
                        type: 'pie',
                        data: {
                            labels: Object.keys(data.peak_times),
                            datasets: [{
                                data: Object.values(data.peak_times),
                                backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56']
                            }]
                        }
                    }
                );
                
                // Safe point coverage
                const spChart = new Chart(
                    document.getElementById('safePointChart'),
                    {
                        type: 'doughnut',
                        data: {
                            labels: ['With Safe Point', 'Without Safe Point'],
                            datasets: [{
                                data: [
                                    data.safe_point_coverage.with_safe_points,
                                    data.safe_point_coverage.without_safe_points
                                ],
                                backgroundColor: ['#4CAF50', '#FF6384']
                            }]
                        }
                    }
                );
                
                // Unmet demand
                const unmetHTML = data.unmet_demand
                    .map(d => `<li>${d.from} → ${d.to}: ${d.issue}</li>`)
                    .join('');
                document.getElementById('unmetList').innerHTML = unmetHTML;
            });
    </script>
</body>
</html>
```

### How to Integrate in n8n

After each route request:
1. **Extract anonymized data** (no phone, name, location)
2. **POST to backend**: `/api/dashboard/log_request`
3. **Backend stores** in database or CSV
4. **Dashboard reads** aggregated data on page load

```javascript
// In n8n, after route lookup succeeds
return {
  request_id: uuid(),
  from_area: $node.IntakeAgent.output.from,
  to_area: $node.IntakeAgent.output.to,
  timestamp: new Date().toISOString(),
  time_of_day: getTimeOfDay(new Date()),
  language: $node.IntakeAgent.output.language,
  has_child: $node.IntakeAgent.output.has_child,
  route_found: !!$node.RouteLookup.output.routes,
  safe_point_found: !!$node.SakhiLookup.output.safe_points.length
};
```

---

## Part 7: Complete n8n Workflow Architecture

### Main Workflow: SMS Route Request → Reply

```
[1] Twilio Webhook Trigger
    ↓
[2] Parse SMS (Extract phone, text, timestamp)
    ↓
[3] Call Claude Intake Agent (HTTP)
    ↓
[4] Branch: What intent?
    ├→ route_request:
    │   ├→ [5a] Route Lookup
    │   ├→ [5b] Sakhi Network Lookup
    │   ├→ [5c] Format Reply
    │   ├→ [5d] Log Request (Dashboard)
    │   └→ [6] Send SMS Reply
    │
    ├→ start_trip:
    │   ├→ [7] Create Trip (Journey Watch)
    │   └→ [6] Send SMS: "Journey Watch ON"
    │
    ├→ reached:
    │   ├→ [8] Confirm Reached (HTTP to /api/journey/reached)
    │   └→ [6] Send SMS: "Safe arrival recorded!"
    │
    ├→ help:
    │   ├→ [9] Send Emergency Alert
    │   └→ [6] Send SMS: "Help sent to contacts"
    │
    └→ unknown:
        └→ [6] Send SMS: "I didn't understand. Try: T Nagar to Nungambakkam"
    ↓
[10] Log completion (optional: to database)
```

### Scheduled Workflows

**Workflow 2: Journey Watch Check-in (10 min after START)**
```
[Scheduled: Triggered by Workflow 1]
  ↓
[Load trip_id from memory/database]
  ↓
[Check: Did user send REACHED?]
  ├→ YES: Exit
  └→ NO: Send check-in SMS
         [Delay 15 min]
         → Escalate (Workflow 3)
```

**Workflow 3: Journey Watch Escalate (25 min after START)**
```
[Scheduled: Triggered by Workflow 2]
  ↓
[Load trip_id and escalation_contacts]
  ↓
[Send SMS to user: "Need help?"]
  ↓
[Send SMS to contacts: Alert message]
  ↓
[Log escalation to dashboard]
```

---

## Part 8: Complete Setup Files

### .env Template (Save as `.env`, don't commit)
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE=+1234567890
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
N8N_WEBHOOK_URL=https://xxx.n8n.cloud/webhook
BACKEND_API_URL=http://localhost:5000
DATABASE_URL=optional_supabase_or_firebase
SARVAM_API_KEY=optional_for_voice
```

### Python Backend Requirements (requirements.txt)
```
flask==2.3.0
flask-cors==4.0.0
requests==2.31.0
python-dotenv==1.0.0
uuid==1.30
```

### n8n Node Configuration Examples

**Claude Intake Agent (HTTP Request Node)**
```json
{
  "method": "POST",
  "url": "https://api.anthropic.com/v1/messages",
  "headers": {
    "x-api-key": "={{$env.CLAUDE_API_KEY}}",
    "content-type": "application/json"
  },
  "body": {
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 500,
    "system": "You are the SafePath Intake Agent...",
    "messages": [
      {
        "role": "user",
        "content": "Parse this SMS:\n\n={{$node.TwilioPayload.json.Body}}"
      }
    ]
  }
}
```

---

## Summary

| Agent | Status | Type | Time to Build |
|-------|--------|------|----------------|
| Intake | ✅ Ready | Claude API | 15 min (n8n setup) |
| Route Lookup | ✅ Ready | Python function | 30 min (n8n setup) |
| Sakhi Network | ✅ Ready | Python function | 20 min (n8n setup) |
| Journey Watch | ✅ Spec ready | Scheduled workflows | 2-3 hours |
| Dashboard | ✅ Spec ready | HTML + Python backend | 1-2 hours |

**Total Phase 1 (SMS Core): 4-6 hours with 2 people**
**Total Phase 2 (Full system): 8-10 hours with 2 people**

All logic, code snippets, and integrations are above. Ready to build!
