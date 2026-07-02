"""
AEGIS-OS Datastore Router — CRUD for all 13 entity types within a Pod.
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from auth.jwt_handler import get_current_user
from auth.rbac import require_investigator
from lemma.datastore import PodDatastore

router = APIRouter(prefix="/pods/{pod_id}/datastore", tags=["Pod Datastore"])

# Per-pod datastore instances
_DATASTORES: Dict[str, PodDatastore] = {}

ENTITY_TYPES = [
    "persons", "locations", "vehicles", "devices", "events",
    "evidence_items", "timeline_events", "hypotheses", "risk_scores",
    "reports", "notes", "cdr_records", "contacts",
]


def _get_ds(pod_id: str) -> PodDatastore:
    if pod_id not in _DATASTORES:
        _DATASTORES[pod_id] = PodDatastore(pod_id)
    return _DATASTORES[pod_id]


class EntityUpsertRequest(BaseModel):
    data: Dict[str, Any]
    entity_id: Optional[str] = None


@router.get("/summary")
async def get_datastore_summary(pod_id: str, current_user: Dict = Depends(get_current_user)):
    """Entity counts per type for this pod."""
    return _get_ds(pod_id).summary()


@router.get("/export")
async def export_datastore(pod_id: str, current_user: Dict = Depends(get_current_user)):
    """Export the entire datastore (all 13 entity types)."""
    return _get_ds(pod_id).export()


@router.get("/{entity_type}")
async def list_entities(
    pod_id: str,
    entity_type: str,
    q: Optional[str] = Query(None, description="Search query"),
    current_user: Dict = Depends(get_current_user),
):
    """List or search entities of a given type."""
    ds = _get_ds(pod_id)
    if entity_type not in ds.ENTITY_TYPES:
        raise HTTPException(400, f"Unknown entity type: {entity_type}. Supported: {sorted(ds.ENTITY_TYPES)}")
    if q:
        entries = ds.search(entity_type, q)
    else:
        entries = ds.list(entity_type)
    return {"entities": [e.to_dict() for e in entries], "count": len(entries)}


@router.post("/{entity_type}", status_code=201)
async def create_entity(
    pod_id: str,
    entity_type: str,
    body: EntityUpsertRequest,
    current_user: Dict = Depends(require_investigator),
):
    """Create or update an entity."""
    ds = _get_ds(pod_id)
    if entity_type not in ds.ENTITY_TYPES:
        raise HTTPException(400, f"Unknown entity type: {entity_type}")
    entry = ds.put(
        entity_type,
        body.data,
        entity_id=body.entity_id,
        created_by=current_user.get("email"),
    )
    return entry.to_dict()


@router.get("/{entity_type}/{entity_id}")
async def get_entity(
    pod_id: str,
    entity_type: str,
    entity_id: str,
    current_user: Dict = Depends(get_current_user),
):
    """Get a single entity by ID."""
    entry = _get_ds(pod_id).get(entity_type, entity_id)
    if not entry:
        raise HTTPException(404, f"{entity_type}/{entity_id} not found.")
    return entry.to_dict()


@router.put("/{entity_type}/{entity_id}")
async def update_entity(
    pod_id: str,
    entity_type: str,
    entity_id: str,
    body: EntityUpsertRequest,
    current_user: Dict = Depends(require_investigator),
):
    """Update an existing entity."""
    ds = _get_ds(pod_id)
    if not ds.get(entity_type, entity_id):
        raise HTTPException(404, f"{entity_type}/{entity_id} not found.")
    entry = ds.put(entity_type, body.data, entity_id=entity_id, created_by=current_user.get("email"))
    return entry.to_dict()


@router.delete("/{entity_type}/{entity_id}")
async def delete_entity(
    pod_id: str,
    entity_type: str,
    entity_id: str,
    current_user: Dict = Depends(require_investigator),
):
    """Soft-delete an entity."""
    deleted = _get_ds(pod_id).delete(entity_type, entity_id)
    if not deleted:
        raise HTTPException(404, f"{entity_type}/{entity_id} not found.")
    return {"message": "Entity deleted.", "entity_id": entity_id}
