"""
AEGIS-OS Lemma SDK — Pod Datastore
====================================
Structured entity store within a Pod.
Manages all investigation entities: persons, locations, events, notes, etc.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypeVar, Generic
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger("aegis.lemma.datastore")

T = TypeVar("T")


@dataclass
class DatastoreEntry:
    id: str
    entity_type: str
    data: Dict[str, Any]
    pod_id: str
    created_at: str
    updated_at: str
    created_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    is_deleted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PodDatastore:
    """
    Lemma Datastore — structured entity storage for an Investigation Pod.

    Supports 13 entity types:
      persons, locations, vehicles, devices, events, evidence_items,
      timeline_events, hypotheses, risk_scores, reports, notes, cdr_records, contacts
    """

    ENTITY_TYPES = {
        "persons", "locations", "vehicles", "devices", "events",
        "evidence_items", "timeline_events", "hypotheses", "risk_scores",
        "reports", "notes", "cdr_records", "contacts",
    }

    def __init__(self, pod_id: str):
        self.pod_id = pod_id
        self._store: Dict[str, Dict[str, DatastoreEntry]] = {
            t: {} for t in self.ENTITY_TYPES
        }

    # ─── CRUD ─────────────────────────────────────────────────────────────────
    def put(self, entity_type: str, data: Dict[str, Any], entity_id: str = None, created_by: str = None) -> DatastoreEntry:
        """Create or update an entity."""
        self._validate_type(entity_type)
        now = datetime.now(timezone.utc).isoformat()
        eid = entity_id or str(uuid.uuid4())
        existing = self._store[entity_type].get(eid)
        entry = DatastoreEntry(
            id=eid,
            entity_type=entity_type,
            data=data,
            pod_id=self.pod_id,
            created_at=existing.created_at if existing else now,
            updated_at=now,
            created_by=created_by or (existing.created_by if existing else None),
            tags=data.get("tags", []),
        )
        self._store[entity_type][eid] = entry
        logger.debug(f"Datastore [{self.pod_id}]: put {entity_type}/{eid}")
        return entry

    def get(self, entity_type: str, entity_id: str) -> Optional[DatastoreEntry]:
        """Retrieve a single entity."""
        self._validate_type(entity_type)
        entry = self._store[entity_type].get(entity_id)
        return entry if entry and not entry.is_deleted else None

    def list(self, entity_type: str, filter_fn=None) -> List[DatastoreEntry]:
        """List all (non-deleted) entities of a type."""
        self._validate_type(entity_type)
        entries = [e for e in self._store[entity_type].values() if not e.is_deleted]
        if filter_fn:
            entries = [e for e in entries if filter_fn(e)]
        return entries

    def delete(self, entity_type: str, entity_id: str) -> bool:
        """Soft-delete an entity."""
        self._validate_type(entity_type)
        entry = self._store[entity_type].get(entity_id)
        if not entry:
            return False
        entry.is_deleted = True
        entry.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def search(self, entity_type: str, query: str) -> List[DatastoreEntry]:
        """Simple full-text search across entity data fields."""
        self._validate_type(entity_type)
        query_lower = query.lower()
        results = []
        for entry in self._store[entity_type].values():
            if entry.is_deleted:
                continue
            data_str = str(entry.data).lower()
            if query_lower in data_str:
                results.append(entry)
        return results

    def count(self, entity_type: str) -> int:
        self._validate_type(entity_type)
        return sum(1 for e in self._store[entity_type].values() if not e.is_deleted)

    def summary(self) -> Dict[str, int]:
        """Return entity counts per type."""
        return {t: self.count(t) for t in self.ENTITY_TYPES}

    def export(self) -> Dict[str, List[Dict]]:
        """Export entire datastore as a serializable dict."""
        return {
            t: [e.to_dict() for e in entries.values() if not e.is_deleted]
            for t, entries in self._store.items()
        }

    def _validate_type(self, entity_type: str) -> None:
        if entity_type not in self.ENTITY_TYPES:
            raise ValueError(
                f"Unknown entity type: '{entity_type}'. "
                f"Supported: {sorted(self.ENTITY_TYPES)}"
            )

    # ─── Convenience helpers ──────────────────────────────────────────────────
    def add_person(self, name: str, role: str = "unknown", **kwargs) -> DatastoreEntry:
        return self.put("persons", {"name": name, "role": role, **kwargs})

    def add_location(self, name: str, lat: float = 0.0, lng: float = 0.0, **kwargs) -> DatastoreEntry:
        return self.put("locations", {"name": name, "lat": lat, "lng": lng, **kwargs})

    def add_hypothesis(self, title: str, description: str, confidence: float = 0.0, **kwargs) -> DatastoreEntry:
        return self.put("hypotheses", {
            "title": title, "description": description,
            "confidence_score": confidence, **kwargs
        })

    def add_timeline_event(self, title: str, timestamp: str, event_type: str, **kwargs) -> DatastoreEntry:
        return self.put("timeline_events", {
            "title": title, "timestamp": timestamp, "event_type": event_type, **kwargs
        })

    def add_note(self, text: str, author: str = "system", **kwargs) -> DatastoreEntry:
        return self.put("notes", {"text": text, "author": author, **kwargs})
