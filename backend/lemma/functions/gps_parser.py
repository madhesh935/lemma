"""Lemma Function: GPS Log Parser"""
import re, json, logging
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger("aegis.fn.gps_parser")

def parse_gps(file_path: str = None, raw_data: str = None) -> Dict[str, Any]:
    """Parse GPS log from GPX file, JSON, CSV, or raw text. Returns normalized waypoints."""
    result: Dict[str, Any] = {
        "waypoints": [], "track_segments": [], "bounds": {},
        "total_distance_km": 0.0, "source_format": "unknown", "error": None
    }
    try:
        if file_path:
            suffix = Path(file_path).suffix.lower()
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            if suffix == ".gpx":
                result = _parse_gpx(content, result)
            elif suffix == ".json":
                result = _parse_json_gps(content, result)
            elif suffix == ".csv":
                result = _parse_csv_gps(content, result)
            else:
                result = _parse_raw_gps(content, result)
        elif raw_data:
            result = _parse_raw_gps(raw_data, result)
        if result["waypoints"]:
            result["bounds"] = _compute_bounds(result["waypoints"])
            result["total_distance_km"] = _compute_distance(result["waypoints"])
    except Exception as e:
        result["error"] = str(e)
    return result

def _parse_gpx(content: str, result: dict) -> dict:
    result["source_format"] = "gpx"
    lat_lons = re.findall(r'lat=["\']([^"\']+)["\'].*?lon=["\']([^"\']+)["\']', content)
    times = re.findall(r'<time>([^<]+)</time>', content)
    elevs = re.findall(r'<ele>([^<]+)</ele>', content)
    for i, (lat, lon) in enumerate(lat_lons):
        wp = {"lat": float(lat), "lng": float(lon), "index": i}
        if i < len(times): wp["timestamp"] = times[i]
        if i < len(elevs): wp["elevation"] = float(elevs[i])
        result["waypoints"].append(wp)
    return result

def _parse_json_gps(content: str, result: dict) -> dict:
    result["source_format"] = "json"
    data = json.loads(content)
    if isinstance(data, list):
        for item in data:
            lat = item.get("lat") or item.get("latitude")
            lng = item.get("lng") or item.get("lon") or item.get("longitude")
            if lat and lng:
                result["waypoints"].append({"lat": float(lat), "lng": float(lng),
                                            "timestamp": item.get("time") or item.get("timestamp", "")})
    return result

def _parse_csv_gps(content: str, result: dict) -> dict:
    import csv, io
    result["source_format"] = "csv"
    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        lat = row.get("lat") or row.get("latitude")
        lng = row.get("lng") or row.get("lon") or row.get("longitude")
        if lat and lng:
            result["waypoints"].append({"lat": float(lat), "lng": float(lng),
                                        "timestamp": row.get("time") or row.get("timestamp", "")})
    return result

def _parse_raw_gps(content: str, result: dict) -> dict:
    result["source_format"] = "raw"
    pattern = r"(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)"
    for m in re.finditer(pattern, content):
        lat, lng = float(m.group(1)), float(m.group(2))
        if -90 <= lat <= 90 and -180 <= lng <= 180:
            result["waypoints"].append({"lat": lat, "lng": lng})
    return result

def _compute_bounds(waypoints):
    lats = [w["lat"] for w in waypoints]
    lngs = [w["lng"] for w in waypoints]
    return {"min_lat": min(lats), "max_lat": max(lats), "min_lng": min(lngs), "max_lng": max(lngs)}

def _compute_distance(waypoints) -> float:
    import math
    total = 0.0
    for i in range(1, len(waypoints)):
        a, b = waypoints[i-1], waypoints[i]
        dlat = math.radians(b["lat"] - a["lat"])
        dlng = math.radians(b["lng"] - a["lng"])
        x = math.sin(dlat/2)**2 + math.cos(math.radians(a["lat"])) * math.cos(math.radians(b["lat"])) * math.sin(dlng/2)**2
        total += 6371 * 2 * math.atan2(math.sqrt(x), math.sqrt(1-x))
    return round(total, 3)
