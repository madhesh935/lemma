"""Lemma Function: Timeline Builder"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import logging, re

logger = logging.getLogger("aegis.fn.timeline")

def build_timeline(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Sort, deduplicate, and resolve conflicting events into a forensic timeline.
    
    Args:
        events: List of dicts with keys: timestamp, type, title, description,
                source, confidence, lat, lng, persons
    Returns:
        { "events": sorted list, "conflicts": list, "gaps": list,
          "first_event": str, "last_event": str, "span_hours": float }
    """
    result = {"events": [], "conflicts": [], "gaps": [], "first_event": "", "last_event": "", "span_hours": 0.0}
    if not events:
        return result

    parsed = []
    for ev in events:
        ts = _parse_timestamp(ev.get("timestamp", ""))
        if ts:
            parsed.append({**ev, "_ts": ts})
        else:
            logger.warning(f"Could not parse timestamp for event: {ev.get('title')}")

    parsed.sort(key=lambda e: e["_ts"])
    
    # Detect conflicts (same type within 5 min with different positions)
    conflicts = []
    for i in range(len(parsed) - 1):
        a, b = parsed[i], parsed[i+1]
        delta = abs((b["_ts"] - a["_ts"]).total_seconds())
        if (delta < 300 and a.get("type") == b.get("type")
                and a.get("lat") and b.get("lat")
                and abs(a["lat"] - b["lat"]) > 0.001):
            conflicts.append({"event_a": a.get("title"), "event_b": b.get("title"),
                               "reason": "Same source type within 5 min but different location"})

    # Detect significant gaps (>6 hours)
    gaps = []
    for i in range(len(parsed) - 1):
        delta_h = (parsed[i+1]["_ts"] - parsed[i]["_ts"]).total_seconds() / 3600
        if delta_h > 6:
            gaps.append({"after": parsed[i].get("title"), "gap_hours": round(delta_h, 1)})

    # Clean output (remove internal _ts key)
    clean = []
    for ev in parsed:
        e = {k: v for k, v in ev.items() if k != "_ts"}
        e["timestamp_iso"] = ev["_ts"].isoformat()
        clean.append(e)

    if clean:
        result["first_event"] = clean[0]["timestamp_iso"]
        result["last_event"] = clean[-1]["timestamp_iso"]
        result["span_hours"] = round(
            (parsed[-1]["_ts"] - parsed[0]["_ts"]).total_seconds() / 3600, 2
        )

    result["events"] = clean
    result["conflicts"] = conflicts
    result["gaps"] = gaps
    return result


def _parse_timestamp(ts: Any) -> Optional[datetime]:
    if not ts:
        return None
    if isinstance(ts, datetime):
        return ts
    ts_str = str(ts).strip()
    formats = [
        "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M:%S", "%d-%m-%Y %H:%M",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(ts_str[:19], fmt)
        except ValueError:
            continue
    return None
