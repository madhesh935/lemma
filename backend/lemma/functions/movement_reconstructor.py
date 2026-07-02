"""Lemma Function: Movement Reconstructor"""
from typing import List, Dict, Any
import logging
logger = logging.getLogger("aegis.fn.movement")

def reconstruct_movement(
    gps_waypoints: List[Dict],
    cdr_towers: List[Dict] = None,
    cctv_sightings: List[Dict] = None,
) -> Dict[str, Any]:
    """
    Reconstruct a person's movement path by fusing GPS, CDR tower pings, and CCTV sightings.
    Returns a fused, chronologically sorted movement path.
    """
    events = []

    for wp in (gps_waypoints or []):
        events.append({
            "source": "gps",
            "timestamp": wp.get("timestamp", ""),
            "lat": wp.get("lat"),
            "lng": wp.get("lng"),
            "confidence": 0.95,
            "label": "GPS waypoint",
        })

    for tower in (cdr_towers or []):
        events.append({
            "source": "cdr",
            "timestamp": tower.get("timestamp", ""),
            "lat": tower.get("lat"),
            "lng": tower.get("lng"),
            "radius_m": tower.get("radius_m", 500),
            "confidence": 0.7,
            "label": f"CDR tower: {tower.get('tower_id','?')}",
        })

    for sighting in (cctv_sightings or []):
        events.append({
            "source": "cctv",
            "timestamp": sighting.get("timestamp", ""),
            "lat": sighting.get("lat"),
            "lng": sighting.get("lng"),
            "camera_id": sighting.get("camera_id", ""),
            "confidence": 0.8,
            "label": f"CCTV: {sighting.get('camera_id','?')}",
        })

    # Sort by timestamp
    def sort_key(e):
        ts = e.get("timestamp", "")
        return ts or "0"

    events.sort(key=sort_key)
    valid = [e for e in events if e.get("lat") is not None and e.get("lng") is not None]

    # Build path for React Leaflet polyline
    path = [[e["lat"], e["lng"]] for e in valid]

    return {
        "movement_events": valid,
        "path": path,
        "total_stops": len(valid),
        "sources_used": list({e["source"] for e in valid}),
        "coverage": {
            "gps": sum(1 for e in valid if e["source"] == "gps"),
            "cdr": sum(1 for e in valid if e["source"] == "cdr"),
            "cctv": sum(1 for e in valid if e["source"] == "cctv"),
        },
    }
