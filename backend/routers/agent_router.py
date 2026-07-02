"""
AEGIS-OS Agent Router — invoke any Lemma agent on demand.
"""
import asyncio
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from lemma.agents import AGENT_REGISTRY, get_agent
from auth.jwt_handler import get_current_user
from auth.rbac import require_investigator
from lemma.functions.notifier import send_notification

router = APIRouter(prefix="/agents", tags=["AI Agents"])

# In-memory job store
_JOBS: Dict[str, Dict] = {}


class InvokeAgentRequest(BaseModel):
    agent_name: str
    pod_id: str
    context: Dict[str, Any] = {}
    async_mode: bool = True


@router.post("/invoke")
async def invoke_agent(
    body: InvokeAgentRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(require_investigator),
):
    """Invoke a specific Lemma agent."""
    agent_name = body.agent_name
    if agent_name not in AGENT_REGISTRY:
        raise HTTPException(400, f"Unknown agent: {agent_name}. Available: {list(AGENT_REGISTRY.keys())}")

    job_id = str(uuid.uuid4())
    _JOBS[job_id] = {
        "job_id": job_id,
        "agent_name": agent_name,
        "pod_id": body.pod_id,
        "status": "pending",
        "output": None,
        "error": None,
        "started_by": current_user.get("email"),
    }

    async def _run():
        _JOBS[job_id]["status"] = "running"
        try:
            agent_cls = get_agent(agent_name)
            agent = agent_cls()
            result = await agent.invoke(body.pod_id, body.context)
            _JOBS[job_id]["status"] = "completed" if result.success else "failed"
            _JOBS[job_id]["output"] = result.output
            _JOBS[job_id]["error"] = result.error
            _JOBS[job_id]["duration_seconds"] = result.duration_seconds
        except Exception as e:
            _JOBS[job_id]["status"] = "failed"
            _JOBS[job_id]["error"] = str(e)

    if body.async_mode:
        background_tasks.add_task(_run)
        return {"job_id": job_id, "status": "pending", "message": f"Agent {agent_name} queued."}
    else:
        await _run()
        return _JOBS[job_id]


@router.get("/status/{job_id}")
async def get_job_status(job_id: str, current_user: Dict = Depends(get_current_user)):
    """Get the status of an agent job."""
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found.")
    return job


@router.get("/history/{pod_id}")
async def get_agent_history(pod_id: str, current_user: Dict = Depends(get_current_user)):
    """Get all agent job history for a pod."""
    jobs = [j for j in _JOBS.values() if j.get("pod_id") == pod_id]
    return {"jobs": jobs, "total": len(jobs)}


@router.get("/list")
async def list_agents(current_user: Dict = Depends(get_current_user)):
    """List all available agents with their descriptions."""
    from lemma.agents.base_agent import BaseAgent
    agents = []
    for name, cls in AGENT_REGISTRY.items():
        agents.append({
            "name": name,
            "description": cls.description,
            "version": cls.version,
            "status": "ready",
        })
    return {"agents": agents}
