"""Lemma Function: Heatmap Generator"""
from typing import List, Dict, Any
import logging
logger = logging.getLogger("aegis.fn.heatmap")

def generate_heatmap(locations: List[Dict[str, Any]], intensity_key: str = "weight") -> Dict[str, Any]:
    """
    Generate GeoJSON heatmap data from a list of locations with optional intensity weights.
    Returns FeatureCollection for Leaflet/Mapbox heatmap layer.
    """
    if not locations:
        return {"type": "FeatureCollection", "features": [], "bounds": None}

    features = []
    lats, lngs = [], []

    for loc in locations:
        lat = loc.get("lat") or loc.get("latitude")
        lng = loc.get("lng") or loc.get("longitude") or loc.get("lon")
        if lat is None or lng is None:
            continue
        lat, lng = float(lat), float(lng)
        lats.append(lat); lngs.append(lng)
        intensity = float(loc.get(intensity_key, 1.0))
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lng, lat]},
            "properties": {
                "intensity": intensity,
                "label": loc.get("label") or loc.get("name", ""),
                "timestamp": loc.get("timestamp", ""),
                "event_type": loc.get("event_type") or loc.get("type", ""),
                **{k: v for k, v in loc.items() if k not in ("lat","lng","latitude","longitude","lon")},
            },
        })

    bounds = None
    if lats:
        bounds = [[min(lats), min(lngs)], [max(lats), max(lngs)]]
        center = [(min(lats) + max(lats)) / 2, (min(lngs) + max(lngs)) / 2]
    else:
        center = [20.5937, 78.9629]  # Default: India center

    return {
        "type": "FeatureCollection",
        "features": features,
        "bounds": bounds,
        "center": center,
        "total_points": len(features),
    }
