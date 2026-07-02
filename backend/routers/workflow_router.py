"""
AEGIS-OS Workflow Router — Investigation Workflow management + SSE feed.
"""
import asyncio
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from lemma.workflows.investigation_workflow import InvestigationWorkflow
from lemma.functions.notifier import get_notifications, send_notification
from auth.jwt_handler import get_current_user
from auth.rbac import require_investigator, require_lead

router = APIRouter(prefix="/workflows", tags=["Investigation Workflow"])

# In-memory workflow instances
_WORKFLOWS: Dict[str, InvestigationWorkflow] = {}
_WORKFLOW_STATES: Dict[str, Dict] = {}


class StartWorkflowRequest(BaseModel):
    pod_id: str
    context: Dict[str, Any] = {}

class ApproveRequest(BaseModel):
    report_type: str = "investigator"


@router.post("/start")
async def start_workflow(
    body: StartWorkflowRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(require_lead),
):
    """Start the investigation workflow for a pod."""
    pod_id = body.pod_id
    if pod_id in _WORKFLOWS and not _WORKFLOWS[pod_id].is_paused:
        return {"message": "Workflow already running.", "state": _WORKFLOWS[pod_id].get_state()}

    workflow = InvestigationWorkflow(pod_id=pod_id)
    _WORKFLOWS[pod_id] = workflow

    async def _run():
        state = await workflow.start(body.context)
        _WORKFLOW_STATES[pod_id] = state

    background_tasks.add_task(_run)
    return {"message": "Workflow started.", "pod_id": pod_id}


@router.get("/{pod_id}/status")
async def get_workflow_status(pod_id: str, current_user: Dict = Depends(get_current_user)):
    """Get current workflow state for a pod."""
    workflow = _WORKFLOWS.get(pod_id)
    if not workflow:
        # Return empty state if not started
        return {
            "pod_id": pod_id,
            "current_step": "not_started",
            "is_paused": False,
            "step_history": [],
            "progress_pct": 0,
        }
    return workflow.get_state()


@router.post("/{pod_id}/approve")
async def approve_workflow(
    pod_id: str,
    body: ApproveRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(require_lead),
):
    """Human approval — advance from review checkpoint to report generation."""
    workflow = _WORKFLOWS.get(pod_id)
    if not workflow:
        raise HTTPException(404, f"No workflow found for pod {pod_id}.")
    if not workflow.is_paused:
        raise HTTPException(400, "Workflow is not at review checkpoint.")

    async def _approve():
        result = await workflow.approve_and_generate_report(
            approved_by=current_user.get("email"),
            report_type=body.report_type,
        )
        _WORKFLOW_STATES[pod_id] = result

    background_tasks.add_task(_approve)
    return {
        "message": "Approval recorded. Generating report in background.",
        "approved_by": current_user.get("email"),
        "report_type": body.report_type,
    }


@router.post("/{pod_id}/advance")
async def manually_advance(
    pod_id: str,
    current_user: Dict = Depends(require_lead),
):
    """Manually advance the workflow step (for recovery)."""
    workflow = _WORKFLOWS.get(pod_id)
    if not workflow:
        raise HTTPException(404, "No workflow found.")
    return {"current_step": workflow.current_step, "state": workflow.get_state()}


@router.get("/feed")
async def workflow_event_feed(
    pod_id: Optional[str] = None,
    current_user: Dict = Depends(get_current_user),
):
    """Server-Sent Events (SSE) stream of live workflow events."""
    async def event_generator():
        last_count = 0
        while True:
            notifications = get_notifications(pod_id=pod_id, last_n=50)
            if len(notifications) > last_count:
                new_events = notifications[last_count:]
                for event in new_events:
                    data = json.dumps(event)
                    yield f"data: {data}\n\n"
                last_count = len(notifications)
            await asyncio.sleep(2)  # Poll every 2 seconds

    return StreamingResponse(event_generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/feed/snapshot")
async def get_feed_snapshot(
    pod_id: Optional[str] = None,
    current_user: Dict = Depends(get_current_user),
):
    """Get the current notification snapshot (for initial page load)."""
    return {"events": get_notifications(pod_id=pod_id, last_n=50)}
