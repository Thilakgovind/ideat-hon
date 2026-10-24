# SafePath n8n Workflow Blueprint

## Core SMS Flow (One Request)

```
SMS Webhook Trigger
       ↓
Parse SMS (phone, text, timestamp)
       ↓
Call Claude Intake Agent
       ↓
Route Lookup (if route_request)
       ↓
Sakhi Network Lookup (if route_request)
       ↓
Format Reply
       ↓
Send SMS Reply
```

## Detailed Node Breakdown

### 1. **Webhook Trigger: Incoming SMS**
**Type:** Webhook (HTTP POST)

**Config:**
- Listen for POST from Twilio (or your gateway)
- Extract: `From` (phone), `Body` (SMS text), `MessageSid` (unique ID)

**Example payload from Twilio:**
```json
{
  "From": "+91 98xxx xxxxx",
  "Body": "T Nagar to Nungambakkam 8 mani paapa",
  "MessageSid": "SM1234567890abcdef",
  "AccountSid": "...",
  "Timestamp": "2024-10-23T10:30:00Z"
}
```

**Output:** `$node["Webhook"].json`

---

### 2. **Parse SMS**
**Type:** Set (or Code)

**What it does:** Extract and clean the SMS data.

**Code:**
```javascript
{
  "phone": $node["Webhook"].json.From,
  "text": $node["Webhook"].json.Body.trim(),
  "message_id": $node["Webhook"].json.MessageSid,
  "timestamp": $node["Webhook"].json.Timestamp,
  "language": "guess_from_text" // Will refine after Intake agent
}
```

**Output:** `$node["Parse SMS"].json`

---

### 3. **Call Claude Intake Agent**
**Type:** HTTP Request (POST)

**Config:**
```
URL: https://api.anthropic.com/v1/messages
Method: POST
Headers:
  - x-api-key: YOUR_CLAUDE_API_KEY
  - content-type: application/json

Body:
{
  "model": "claude-3-5-sonnet-20241022",
  "max_tokens": 500,
  "system": "[PASTE INTAKE_AGENT_PROMPT.md HERE]",
  "messages": [
    {
      "role": "user",
      "content": "Parse this SMS:\n\n{{ $node[\"Parse SMS\"].json.text }}"
    }
  ]
}
```

**Response parsing:**
```javascript
// Extract JSON from Claude's response
const response = $node["Call Intake Agent"].json.content[0].text;
// Claude returns raw JSON; parse it
return JSON.parse(response);
```

**Output:** `$node["Intake Result"].json` with fields:
- `intent`
- `from`
- `to`
- `time`
- `language`
- `has_child`
- `confidence`

---

### 4. **Route Lookup (Conditional)**
**Type:** Function (Code)

**Condition:** Only run if `intent === "route_request"` and `from` + `to` are not null

**What it does:**
1. Load `routes.json`
2. Fuzzy-match `from` and `to` to actual stop names
3. Find **free buses first**, then alternatives
4. Return best 2 routes with stop names, numbers, frequency, next departure estimate

**Code:**
```javascript
const routes = require('./data/routes.json').routes;
const from = $node["Intake Result"].json.from;
const to = $node["Intake Result"].json.to;
const time = $node["Intake Result"].json.time;

// Fuzzy match stops (simplified)
function matchStop(userInput) {
  return routes.flatMap(r => r.stops).find(s => 
    s.name.toLowerCase().includes(userInput.toLowerCase()) ||
    s.code.toLowerCase().includes(userInput.toLowerCase())
  );
}

const fromStop = matchStop(from);
const toStop = matchStop(to);

if (!fromStop || !toStop) {
  return { error: "Could not find stops", from, to };
}

// Find routes that go from fromStop to toStop
const matchedRoutes = routes.filter(r => {
  const stops = r.stops.map(s => s.code);
  const fromIdx = stops.indexOf(fromStop.code);
  const toIdx = stops.indexOf(toStop.code);
  return fromIdx >= 0 && fromIdx < toIdx;
});

// Sort: free first, then by frequency
matchedRoutes.sort((a, b) => {
  if (a.is_free !== b.is_free) return b.is_free - a.is_free;
  return a.frequency_minutes - b.frequency_minutes;
});

// Return top 2
return {
  from_stop: fromStop.name,
  to_stop: toStop.name,
  routes: matchedRoutes.slice(0, 2).map(r => ({
    number: r.number,
    is_free: r.is_free,
    frequency: r.frequency_minutes,
    notes: r.notes
  }))
};
```

**Output:** `$node["Route Lookup"].json`

---

### 5. **Sakhi Network Lookup (Conditional)**
**Type:** Function (Code)

**Condition:** Only run if `intent === "route_request"` AND route lookup succeeded

**What it does:**
1. Load `safe_points.json`
2. Find safe waiting points near the boarding stop
3. Check hours (is it safe at the requested time?)
4. Return name, type, hours, location description

**Code:**
```javascript
const safePoints = require('./data/safe_points.json').safe_points;
const boardingStopCode = 
  $node["Route Lookup"].json.routes[0].number; // Placeholder; in reality, get from route

// Get the actual stop code from routes.json
const routes = require('./data/routes.json').routes;
const route = routes.find(r => r.number === boardingStopCode);
const stopCode = route.stops[0].code; // First stop of the chosen route

// Find safe points at this stop
const nearbyPoints = safePoints.filter(sp => sp.stop_code === stopCode);

return {
  boarding_stop: stopCode,
  safe_points: nearbyPoints.map(sp => ({
    name: sp.name,
    type: sp.type,
    hours_safe: sp.hours_safe,
    location: sp.location_description,
    operator: sp.operator_type
  }))
};
```

**Output:** `$node["Sakhi Lookup"].json`

---

### 6. **Format Reply (Set)**
**Type:** Set / Function

**What it does:** Build a human-readable SMS reply in Tamil / English

**Code (simplified):**
```javascript
const intake = $node["Intake Result"].json;
const routes = $node["Route Lookup"].json;
const sakhi = $node["Sakhi Lookup"].json;

let reply = "";

if (intake.intent === "route_request") {
  const route = routes.routes[0];
  const safePoint = sakhi.safe_points[0];
  
  reply = `
  ${route.number} bus (${route.is_free ? "FREE" : "PAID"})
  ${routes.from_stop} → ${routes.to_stop}
  Every ${route.frequency} min
  ${safePoint ? `Wait at: ${safePoint.name} (${safePoint.hours_safe})` : ""}
  
  Reply START when you leave.
  Reply HELP anytime.
  `;
} else if (intake.intent === "start_trip") {
  reply = "Your Journey Watch is ON. Reply REACHED when you arrive.";
} else if (intake.intent === "reached") {
  reply = "Safe reach confirmed. Thank you for using SafePath.";
} else if (intake.intent === "help") {
  reply = "Help alert sent to your contacts. Please call 112 or 181 if in danger.";
}

return {
  to: $node["Parse SMS"].json.phone,
  message: reply.trim()
};
```

**Output:** `$node["Format Reply"].json` with `to` and `message`

---

### 7. **Send SMS Reply**
**Type:** HTTP Request (POST to Twilio Send)

**Config:**
```
URL: https://api.twilio.com/2010-04-01/Accounts/{{ YOUR_ACCOUNT_SID }}/Messages.json
Method: POST
Auth: Basic (Account SID : Auth Token)

Body:
{
  "From": "{{ TWILIO_PHONE }}",
  "To": "{{ $node[\"Format Reply\"].json.to }}",
  "Body": "{{ $node[\"Format Reply\"].json.message }}"
}
```

**Output:** `$node["Send Reply"].json` with Twilio's response

---

### 8. **Log to Database (Optional)**
**Type:** HTTP POST or direct Supabase/JSON file write

**What it does:** Store the request (anonymized) for the policy dashboard

**Payload:**
```json
{
  "timestamp": "$node[\"Parse SMS\"].json.timestamp",
  "from_area": "$node[\"Intake Result\"].json.from",
  "to_area": "$node[\"Intake Result\"].json.to",
  "intent": "$node[\"Intake Result\"].json.intent",
  "bus_used": "$node[\"Route Lookup\"].json.routes[0].number",
  "is_free": "$node[\"Route Lookup\"].json.routes[0].is_free",
  "phone_hash": "hash_of_phone_for_deduplication"
}
```

---

## Error Handling

**If Claude returns unparseable JSON:**
→ Fallback to a simple generic response and log the error

**If no matching routes:**
→ Reply: "I couldn't find a bus on that route. Try a nearby stop or call 112."

**If SMS is empty or garbage:**
→ Don't reply; log and skip

---

## Testing the Workflow

1. **Create the workflow in n8n:**
   - Use the nodes listed above
   - Connect them in sequence

2. **Webhook setup:**
   - In n8n: Webhook → copy the Public URL
   - In Twilio: Incoming webhook URL = n8n Public URL + `/webhook`
   - Test with a sample SMS

3. **Test SMS:**
   - Send: `"T Nagar to Nungambakkam 8 mani"`
   - Expect back within 5 seconds:
     ```
     21G bus (FREE)
     T. Nagar → Nungambakkam
     Every 15 min
     Wait at: Lakshmi Tea Stall (6:00-20:00)
     Reply START when you leave.
     ```

---

## Next Steps

1. **Set up Twilio trial account** and get a phone number
2. **Get Claude API key** from Anthropic
3. **Build nodes 1-7 in n8n** using the spec above
4. **Test with 5 sample SMS** (route requests, START, REACHED, HELP)
5. **Add Journey Watch workflow** (separate scheduled workflow for timers)
