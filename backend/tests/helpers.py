"""Shared test helpers: the demo pair now runs on real MTC buses (data/gtfs_bus.json)."""
import re

from backend import data

REAL_BUSES = {r["number"] for r in data.gtfs_buses()}


def sms_bus(text: str):
    """Bus number in a 'BUS <number> at <stop>' SMS, or None."""
    m = re.search(r"BUS (.+?) at ", text or "")
    return m.group(1) if m else None
