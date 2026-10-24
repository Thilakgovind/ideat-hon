#!/usr/bin/env python
"""
Route Lookup & Sakhi Network Lookup
Standalone functions that work in n8n or locally.
"""

import json
from difflib import SequenceMatcher
from pathlib import Path

# Load data
DATA_DIR = Path(__file__).parent.parent / "data"

with open(DATA_DIR / "routes.json") as f:
    ROUTES_DATA = json.load(f)["routes"]

with open(DATA_DIR / "safe_points.json") as f:
    SAFE_POINTS_DATA = json.load(f)["safe_points"]


def fuzzy_match(user_input, candidates, threshold=0.5):
    """
    Find the best matching candidate string.
    Returns (matched_item, score) or (None, 0) if no match above threshold.
    Prefers prefix matches and code matches over loose fuzzy matching.
    """
    user_lower = user_input.lower().strip()
    user_words = user_lower.split()
    best_match = None
    best_score = 0

    for candidate in candidates:
        name_lower = candidate["name"].lower()
        code_lower = candidate["code"].lower() if "code" in candidate else ""

        # Priority 1: Exact match
        if user_lower == name_lower or user_lower == code_lower:
            return candidate, 1.0

        # Priority 2: Code match (much more reliable)
        if user_lower == code_lower:
            score = 0.99
        # Priority 3: Prefix match on first word
        elif any(name_lower.startswith(word) for word in user_words) or code_lower.startswith(user_lower):
            score = 0.95
        # Priority 4: All user words in candidate name in order
        elif all(word in name_lower for word in user_words):
            score = 0.88
        # Priority 5: Fuzzy matching, but less weight
        else:
            name_score = SequenceMatcher(None, user_lower, name_lower).ratio()
            code_score = SequenceMatcher(None, user_lower, code_lower).ratio()
            score = max(name_score, code_score) * 0.8  # Down-weight fuzzy matches

        if score > best_score:
            best_score = score
            best_match = candidate

    if best_score >= threshold:
        return best_match, best_score
    return None, best_score


def find_route(from_area, to_area, preference="free_first"):
    """
    Find a bus route from from_area to to_area.

    Args:
        from_area: string like "T. Nagar" or "T Nagar"
        to_area: string like "Nungambakkam"
        preference: "free_first" (default) or "fastest"

    Returns:
        {
            "from_stop": "T. Nagar",
            "to_stop": "Nungambakkam",
            "routes": [
                {
                    "number": "21G",
                    "is_free": true,
                    "frequency_minutes": 15,
                    "notes": "Free ordinary bus, runs every 15-20 min",
                    "stop_sequence": ["TND", "RMN", "TEN", "NMB"]
                }
            ]
        }
    """

    # Build a searchable list of all stops
    all_stops = []
    for route in ROUTES_DATA:
        for stop in route["stops"]:
            all_stops.append({
                "name": stop["name"],
                "code": stop["code"],
                "route_id": route["id"]
            })

    # Match from_area
    from_match, from_score = fuzzy_match(from_area, all_stops, threshold=0.6)
    if not from_match:
        return {
            "error": f"Could not match starting area '{from_area}'",
            "from_area": from_area,
            "to_area": to_area
        }

    # Match to_area
    to_match, to_score = fuzzy_match(to_area, all_stops, threshold=0.6)
    if not to_match:
        return {
            "error": f"Could not match destination '{to_area}'",
            "from_area": from_area,
            "to_area": to_area
        }

    from_code = from_match["code"]
    to_code = to_match["code"]

    # Find routes that connect from_code to to_code
    connecting_routes = []

    for route in ROUTES_DATA:
        stop_codes = [s["code"] for s in route["stops"]]

        if from_code in stop_codes and to_code in stop_codes:
            from_idx = stop_codes.index(from_code)
            to_idx = stop_codes.index(to_code)

            if from_idx < to_idx:  # Route goes in the right direction
                connecting_routes.append({
                    "number": route["number"],
                    "is_free": route["is_free"],
                    "frequency_minutes": route["frequency_minutes"],
                    "notes": route["notes"],
                    "stop_sequence": stop_codes[from_idx:to_idx+1],
                    "operator": route["operator"]
                })

    if not connecting_routes:
        return {
            "error": f"No direct route from {from_match['name']} to {to_match['name']}",
            "from_stop": from_match["name"],
            "to_stop": to_match["name"],
            "alternatives": []
        }

    # Sort: free first (if preference == "free_first"), then by frequency
    if preference == "free_first":
        connecting_routes.sort(key=lambda r: (-r["is_free"], r["frequency_minutes"]))
    else:
        connecting_routes.sort(key=lambda r: (r["frequency_minutes"], -r["is_free"]))

    return {
        "from_stop": from_match["name"],
        "to_stop": to_match["name"],
        "routes": connecting_routes[:2]  # Return top 2
    }


def find_safe_points(stop_code):
    """
    Find safe waiting points near a bus stop.

    Args:
        stop_code: string like "NMB" or "TEN"

    Returns:
        {
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
    """

    nearby = [sp for sp in SAFE_POINTS_DATA if sp["stop_code"] == stop_code]

    if not nearby:
        return {
            "stop_code": stop_code,
            "safe_points": [],
            "message": "No verified safe points at this stop yet. Use a well-lit, busy area."
        }

    return {
        "stop_code": stop_code,
        "safe_points": [
            {
                "name": sp["name"],
                "type": sp["type"],
                "operator_type": sp["operator_type"],
                "hours_safe": sp["hours_safe"],
                "location_description": sp["location_description"]
            }
            for sp in nearby
        ]
    }


def format_reply_tamil(route_result, sakhi_result):
    """
    Format a friendly SMS reply in Tamil/English (ASCII-safe, no emojis for SMS).
    """

    if "error" in route_result:
        return f"Sorry, {route_result['error']}\nTry another stop nearby."

    routes = route_result.get("routes", [])
    if not routes:
        return "Sorry, I couldn't find a route. Try another combination of stops."

    route = routes[0]
    from_stop = route_result["from_stop"]
    to_stop = route_result["to_stop"]

    status = "FREE" if route['is_free'] else "PAID"
    msg = f"""BUS {route['number']} [{status}]
{from_stop} -> {to_stop}
Every {route['frequency_minutes']} min

"""

    safe_points = sakhi_result.get("safe_points", [])
    if safe_points:
        sp = safe_points[0]
        msg += f"Wait at: {sp['name']}\n({sp['location_description']})\n\n"

    msg += """Reply START when you board.
Reply REACHED when you arrive.
Reply HELP anytime."""

    return msg


# Test locally
if __name__ == "__main__":
    print("=" * 60)
    print("TEST 1: Route lookup (T. Nagar to Nungambakkam)")
    print("=" * 60)
    result = find_route("T Nagar", "Nungambakkam")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)
    print("TEST 2: Find safe points at Nungambakkam")
    print("=" * 60)
    if result.get("routes"):
        stop_code = result["routes"][0]["stop_sequence"][-1]
        sakhi = find_safe_points(stop_code)
        print(json.dumps(sakhi, indent=2, ensure_ascii=False))

        print("\n" + "=" * 60)
        print("TEST 3: Format reply")
        print("=" * 60)
        reply = format_reply_tamil(result, sakhi)
        print(reply)

    print("\n" + "=" * 60)
    print("TEST 4: Fuzzy matching (wrong spelling)")
    print("=" * 60)
    result2 = find_route("T Nagar", "Teynampet")
    print(json.dumps(result2, indent=2, ensure_ascii=False))
