"""
AEGIS-OS Pod Router — Investigation Pod CRUD.
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from lemma.pod import InvestigationPod, PodManager, PodStatus
from auth.jwt_handler import get_current_user
from auth.rbac import require_investigator, require_lead
from lemma.functions.notifier import send_notification, get_notifications

router = APIRouter(prefix="/pods", tags=["Investigation Pods"])

# In-memory pod store (PostgreSQL in production)
_POD_STORE: Dict[str, Dict] = {}


class CreatePodRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    severity: str = "medium"
    district: Optional[str] = None
    fir_number: Optional[str] = None
    pod_key: Optional[str] = None

class UpdatePodRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None


@router.post("", status_code=201)
async def create_pod(
    body: CreatePodRequest,
    current_user: Dict = Depends(require_lead),
):
    """Create a new Investigation Pod (one per case)."""
    pod = InvestigationPod.create(
        name=body.name,
        pod_key=body.pod_key,
        description=body.description or "",
        severity=body.severity,
        district=body.district,
        fir_number=body.fir_number,
        investigators=[current_user.get("email")],
    )
    PodManager.register(pod)
    pod_dict = pod.to_summary()
    _POD_STORE[pod.pod_id] = pod_dict

    send_notification(
        "pod_created", f"New Investigation Pod: {pod.pod_key}",
        f"Case '{pod.name}' created by {current_user.get('full_name','?')}",
        pod_id=pod.pod_id, severity="info"
    )
    return pod_dict


@router.get("")
async def list_pods(current_user: Dict = Depends(get_current_user)):
    """List all investigation pods."""
    pods = list(_POD_STORE.values())
    # Sort by created_at descending
    pods.sort(key=lambda p: p.get("created_at",""), reverse=True)
    return {"pods": pods, "total": len(pods)}


@router.get("/{pod_id}")
async def get_pod(pod_id: str, current_user: Dict = Depends(get_current_user)):
    """Get a specific pod's state."""
    pod = _POD_STORE.get(pod_id)
    if not pod:
        raise HTTPException(404, f"Pod {pod_id} not found.")
    # Include notification feed
    notifications = get_notifications(pod_id=pod_id, last_n=20)
    return {**pod, "recent_notifications": notifications}


@router.patch("/{pod_id}")
async def update_pod(
    pod_id: str,
    body: UpdatePodRequest,
    current_user: Dict = Depends(require_investigator),
):
    """Update pod metadata."""
    pod = _POD_STORE.get(pod_id)
    if not pod:
        raise HTTPException(404, f"Pod {pod_id} not found.")
    if body.name:
        pod["name"] = body.name
    if body.severity:
        pod["severity"] = body.severity
    if body.status:
        pod["status"] = body.status
    pod["updated_at"] = datetime.now(timezone.utc).isoformat()
    _POD_STORE[pod_id] = pod
    return pod


@router.post("/{pod_id}/archive")
async def archive_pod(
    pod_id: str,
    current_user: Dict = Depends(require_lead),
):
    """Archive an investigation pod."""
    pod = _POD_STORE.get(pod_id)
    if not pod:
        raise HTTPException(404, f"Pod {pod_id} not found.")
    pod["status"] = PodStatus.archived.value
    pod["closed_at"] = datetime.now(timezone.utc).isoformat()
    _POD_STORE[pod_id] = pod
    send_notification("pod_archived", f"Pod Archived: {pod.get('pod_key','?')}",
                     "Investigation has been archived.", pod_id=pod_id, severity="info")
    return {"message": "Pod archived.", "pod_id": pod_id}


@router.get("/{pod_id}/notifications")
async def get_pod_notifications(pod_id: str, current_user: Dict = Depends(get_current_user)):
    """Get workflow notifications for a pod."""
    return {"notifications": get_notifications(pod_id=pod_id, last_n=50)}


@router.get("/stats/summary")
async def get_stats_summary(current_user: Dict = Depends(get_current_user)):
    """Dashboard stats — pod counts by status and severity."""
    pods = list(_POD_STORE.values())
    return {
        "total": len(pods),
        "active": sum(1 for p in pods if p.get("status") == "active"),
        "archived": sum(1 for p in pods if p.get("status") == "archived"),
        "high_risk": sum(1 for p in pods if p.get("severity") in ("high","critical")),
        "critical": sum(1 for p in pods if p.get("severity") == "critical"),
        "by_severity": {
            "critical": sum(1 for p in pods if p.get("severity") == "critical"),
            "high": sum(1 for p in pods if p.get("severity") == "high"),
            "medium": sum(1 for p in pods if p.get("severity") == "medium"),
            "low": sum(1 for p in pods if p.get("severity") == "low"),
        }
    }
