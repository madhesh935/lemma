"""Lemma Function: File Metadata Extractor"""
from __future__ import annotations
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("aegis.fn.metadata")


def extract_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extract metadata from any supported file type.

    Returns EXIF for images, container info for videos,
    document properties for PDFs, and basic OS stats for all.
    """
    result: Dict[str, Any] = {
        "file_name": Path(file_path).name,
        "file_size_bytes": 0,
        "created": "",
        "modified": "",
        "mime_type": "",
        "specific": {},
        "error": None,
    }

    if not os.path.exists(file_path):
        result["error"] = f"File not found: {file_path}"
        return result

    stat = os.stat(file_path)
    result["file_size_bytes"] = stat.st_size
    result["modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
    result["created"] = datetime.fromtimestamp(stat.st_ctime).isoformat()

    suffix = Path(file_path).suffix.lower()

    if suffix in (".jpg", ".jpeg", ".png", ".tiff", ".bmp"):
        result["specific"] = _extract_exif(file_path)
        result["mime_type"] = f"image/{suffix.lstrip('.')}"

    elif suffix == ".pdf":
        result["specific"] = _extract_pdf_meta(file_path)
        result["mime_type"] = "application/pdf"

    elif suffix in (".mp4", ".avi", ".mkv", ".mov"):
        result["specific"] = _extract_video_meta(file_path)
        result["mime_type"] = f"video/{suffix.lstrip('.')}"

    elif suffix == ".json":
        result["specific"] = _extract_json_meta(file_path)
        result["mime_type"] = "application/json"

    elif suffix == ".csv":
        result["specific"] = _extract_csv_meta(file_path)
        result["mime_type"] = "text/csv"

    return result


def _extract_exif(file_path: str) -> Dict:
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
        img = Image.open(file_path)
        exif_data = img._getexif() or {}
        readable = {}
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if isinstance(value, (str, int, float)):
                readable[str(tag)] = value
        readable["image_size"] = f"{img.width}x{img.height}"
        readable["image_mode"] = img.mode
        return readable
    except Exception:
        return {}


def _extract_pdf_meta(file_path: str) -> Dict:
    try:
        import pypdf
        reader = pypdf.PdfReader(file_path)
        meta = reader.metadata or {}
        return {
            "pages": len(reader.pages),
            "title": str(meta.get("/Title", "")),
            "author": str(meta.get("/Author", "")),
            "creator": str(meta.get("/Creator", "")),
            "creation_date": str(meta.get("/CreationDate", "")),
        }
    except Exception:
        return {}


def _extract_video_meta(file_path: str) -> Dict:
    try:
        import subprocess, json as j
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-show_format", file_path
        ]
        out = subprocess.check_output(cmd, timeout=15)
        data = j.loads(out)
        fmt = data.get("format", {})
        streams = data.get("streams", [])
        video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
        return {
            "duration_seconds": float(fmt.get("duration", 0)),
            "format": fmt.get("format_name", ""),
            "bit_rate": fmt.get("bit_rate", ""),
            "codec": video_stream.get("codec_name", ""),
            "resolution": f"{video_stream.get('width', 0)}x{video_stream.get('height', 0)}",
            "frame_rate": video_stream.get("r_frame_rate", ""),
        }
    except Exception:
        return {}


def _extract_json_meta(file_path: str) -> Dict:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return {"type": "array", "records": len(data)}
        elif isinstance(data, dict):
            return {"type": "object", "keys": list(data.keys())[:20]}
        return {"type": type(data).__name__}
    except Exception:
        return {}


def _extract_csv_meta(file_path: str) -> Dict:
    try:
        import csv
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            headers = next(reader, [])
            row_count = sum(1 for _ in reader)
        return {"columns": headers[:30], "row_count": row_count, "column_count": len(headers)}
    except Exception:
        return {}
