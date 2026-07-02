"""
AEGIS-OS Lemma SDK — Evidence File Manager
==========================================
Handles upload, storage, retrieval, and chain-of-custody tracking for
all forensic evidence files ingested into an Investigation Pod.

Supported file types:
  Documents:  PDF, TXT, DOCX
  Data:       JSON, CSV
  Images:     JPG, PNG, TIFF, BMP
  Video:      MP4, AVI, MKV, MOV
  GPS:        GPX, KML
"""
from __future__ import annotations

import hashlib
import mimetypes
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import logging

from config import STORAGE_BACKEND, STORAGE_LOCAL_PATH

logger = logging.getLogger("aegis.lemma.files")


# ─── Supported MIME types ─────────────────────────────────────────────────────
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/json",
    "text/csv",
    "application/csv",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/bmp",
    "video/mp4",
    "video/avi",
    "video/x-matroska",
    "video/quicktime",
    "application/gpx+xml",
    "application/vnd.google-earth.kml+xml",
    "application/octet-stream",  # fallback
}

MAX_FILE_SIZE_MB = 500


@dataclass
class ChainOfCustodyEntry:
    timestamp: str
    action: str          # uploaded | accessed | processed | transferred
    user_id: Optional[str]
    agent_name: Optional[str]
    notes: str = ""


@dataclass
class FileRecord:
    """A single evidence file record in the Pod."""
    file_id: str
    pod_id: str
    original_name: str
    stored_path: str
    file_hash: str                     # SHA-256
    file_size: int                     # bytes
    mime_type: str
    evidence_type: str                 # autopsy_report | image | cctv_video | ...
    uploaded_by: Optional[str] = None
    uploaded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    chain_of_custody: List[ChainOfCustodyEntry] = field(default_factory=list)
    is_processed: bool = False
    processing_notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_id": self.file_id,
            "pod_id": self.pod_id,
            "original_name": self.original_name,
            "file_hash": self.file_hash,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "evidence_type": self.evidence_type,
            "uploaded_by": self.uploaded_by,
            "uploaded_at": self.uploaded_at,
            "is_processed": self.is_processed,
            "chain_of_custody": [
                {"timestamp": e.timestamp, "action": e.action,
                 "user_id": e.user_id, "agent_name": e.agent_name, "notes": e.notes}
                for e in self.chain_of_custody
            ],
            "metadata": self.metadata,
        }

    def add_custody_entry(self, action: str, user_id: str = None, agent_name: str = None, notes: str = "") -> None:
        self.chain_of_custody.append(ChainOfCustodyEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            user_id=user_id,
            agent_name=agent_name,
            notes=notes,
        ))


def _compute_sha256(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def _detect_evidence_type(filename: str, mime_type: str) -> str:
    name_lower = filename.lower()
    if "autopsy" in name_lower or "post_mortem" in name_lower or "pm_" in name_lower:
        return "autopsy_report"
    if "witness" in name_lower or "statement" in name_lower:
        return "witness_statement"
    if "cdr" in name_lower or "call" in name_lower:
        return "call_detail_record"
    if "gps" in name_lower or name_lower.endswith(".gpx"):
        return "gps_log"
    if "cctv" in name_lower or "surveillance" in name_lower:
        return "cctv_video"
    if "medical" in name_lower:
        return "medical_report"
    if mime_type.startswith("image/"):
        return "image"
    if mime_type.startswith("video/"):
        return "video"
    if mime_type == "application/pdf":
        return "pdf"
    if mime_type in ("application/json", "text/csv", "application/csv"):
        return "json_data" if "json" in mime_type else "csv_data"
    return "other"


class PodFiles:
    """
    Lemma Files — Manages evidence file storage for an Investigation Pod.
    """

    def __init__(self, pod_id: str):
        self.pod_id = pod_id
        self.base_dir = Path(STORAGE_LOCAL_PATH) / pod_id
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._records: Dict[str, FileRecord] = {}

    async def upload(
        self,
        file_content: bytes,
        original_name: str,
        mime_type: Optional[str] = None,
        uploaded_by: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> FileRecord:
        """
        Store an evidence file and create a FileRecord with chain-of-custody.
        """
        # Detect MIME type if not provided
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(original_name)
            mime_type = mime_type or "application/octet-stream"

        # Validate size
        size_mb = len(file_content) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise ValueError(f"File too large: {size_mb:.1f} MB (max {MAX_FILE_SIZE_MB} MB)")

        # Generate unique storage name
        file_id = str(uuid.uuid4())
        ext = Path(original_name).suffix
        stored_name = f"{file_id}{ext}"
        stored_path = self.base_dir / stored_name

        # Write file
        with open(stored_path, "wb") as f:
            f.write(file_content)

        # Compute hash
        file_hash = _compute_sha256(str(stored_path))
        evidence_type = _detect_evidence_type(original_name, mime_type)

        record = FileRecord(
            file_id=file_id,
            pod_id=self.pod_id,
            original_name=original_name,
            stored_path=str(stored_path),
            file_hash=file_hash,
            file_size=len(file_content),
            mime_type=mime_type,
            evidence_type=evidence_type,
            uploaded_by=uploaded_by,
            metadata=metadata or {},
        )
        record.add_custody_entry("uploaded", user_id=uploaded_by, notes="Initial upload")
        self._records[file_id] = record

        logger.info(f"File uploaded to pod {self.pod_id}: {original_name} → {file_id} ({evidence_type})")
        return record

    def get(self, file_id: str) -> Optional[FileRecord]:
        return self._records.get(file_id)

    def list(self) -> List[FileRecord]:
        return list(self._records.values())

    def delete(self, file_id: str, user_id: Optional[str] = None) -> bool:
        record = self._records.get(file_id)
        if not record:
            return False
        try:
            Path(record.stored_path).unlink(missing_ok=True)
        except Exception:
            pass
        del self._records[file_id]
        logger.info(f"File {file_id} deleted from pod {self.pod_id} by {user_id}")
        return True

    def read_bytes(self, file_id: str, accessing_agent: Optional[str] = None) -> Optional[bytes]:
        """Read file contents and log chain-of-custody access."""
        record = self._records.get(file_id)
        if not record:
            return None
        record.add_custody_entry("accessed", agent_name=accessing_agent)
        with open(record.stored_path, "rb") as f:
            return f.read()

    def stats(self) -> Dict[str, Any]:
        total = len(self._records)
        size_total = sum(r.file_size for r in self._records.values())
        by_type: Dict[str, int] = {}
        for r in self._records.values():
            by_type[r.evidence_type] = by_type.get(r.evidence_type, 0) + 1
        return {
            "total_files": total,
            "total_size_bytes": size_total,
            "by_type": by_type,
        }
