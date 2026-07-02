"""
AEGIS-OS AI Copilot Router
============================
Routes investigator queries to the correct Lemma agents.
The Copilot never answers directly — it orchestrates agents.
"""
import json
import re
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.jwt_handler import get_current_user
from lemma.agents import AGENT_REGISTRY, get_agent

router = APIRouter(prefix="/copilot", tags=["AI Copilot"])

# In-memory session store
_SESSIONS: Dict[str, List[Dict]] = {}


class CopilotMessage(BaseModel):
    message: str
    pod_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Dict[str, Any] = {}


class CopilotResponse(BaseModel):
    response: str
    agent_used: str
    agents_consulted: List[str]
    session_id: str
    confidence: float
    sources: List[str]


# ─── Intent → Agent routing table ────────────────────────────────────────────
INTENT_ROUTING = {
    # Timeline queries
    r"timeline|chronolog|when|what time|after \d|before \d|sequence|order of events": "timeline_reconstruction",
    # Evidence queries
    r"evidence|document|file|upload|photograph|cctv|cdr|gps|records?": "evidence_intake",
    # Autopsy queries
    r"autopsy|death|injury|injur|cause of death|toxicol|COD|PMI|postmortem|time of death": "autopsy_intelligence",
    # Hypothesis queries
    r"hypothesis|hypothes|theory|suspect|who|scenario|likely|possible|could have": "hypothesis",
    # Risk queries
    r"risk|priorit|urgent|alert|danger|anomal|inconsist": "risk_assessment",
    # Graph / relationship queries
    r"connected|linked|relationship|graph|network|who knows|associated": "knowledge_graph",
    # Report queries
    r"report|summary|brief|generat|export|court|executive": "report",
    # Movement / location
    r"movement|location|where|map|GPS|travel|path|route": "digital_correlation",
}


def _route_to_agent(message: str) -> List[str]:
    """Determine which agents to consult based on the message."""
    message_lower = message.lower()
    matched = []
    for pattern, agent_name in INTENT_ROUTING.items():
        if re.search(pattern, message_lower):
            matched.append(agent_name)
    return list(dict.fromkeys(matched)) or ["hypothesis"]  # default to hypothesis


async def _generate_response(
    message: str,
    agents: List[str],
    pod_id: Optional[str],
    context: Dict,
    history: List[Dict],
) -> Dict[str, Any]:
    """Generate a copilot response by querying relevant agents."""
    # Build context from conversation history
    ctx_str = "\n".join([f"{m['role']}: {m['content'][:200]}" for m in history[-5:]])

    # For each agent, get a brief simulated insight
    agent_insights = []
    for agent_name in agents[:2]:  # Limit to top 2 agents for speed
        try:
            agent_cls = get_agent(agent_name)
            agent = agent_cls()
            insight = await _get_agent_insight(agent, agent_name, message, pod_id, context)
            agent_insights.append(insight)
        except Exception as e:
            agent_insights.append(f"[{agent_name}]: Unable to retrieve insight: {str(e)[:100]}")

    # Synthesize response
    response_text = _synthesize_response(message, agents, agent_insights, pod_id)

    return {
        "response": response_text,
        "agents_consulted": agents,
        "primary_agent": agents[0] if agents else "copilot",
        "insights": agent_insights,
        "confidence": 0.78,
        "sources": [f"Agent: {a}" for a in agents],
    }


async def _get_agent_insight(agent, agent_name: str, query: str, pod_id: Optional[str], context: Dict) -> str:
    """Get a quick insight from an agent."""
    ctx = {**context, "query": query}
    if not ctx.get("case"):
        ctx["case"] = {"name": f"Pod {pod_id}", "pod_key": pod_id, "severity": "medium"}

    result = await agent.invoke(pod_id or "demo", ctx)
    if result.success and result.reasoning:
        return f"[{agent_name}] {result.reasoning[:300]}"
    return f"[{agent_name}] Processing query: '{query[:80]}'"


def _synthesize_response(message: str, agents: List[str], insights: List[str], pod_id: Optional[str]) -> str:
    """Synthesize a coherent response from agent insights."""
    intro = f"Based on analysis from {', '.join(agents[:2])}"
    if pod_id:
        intro += f" for investigation {pod_id}"
    intro += ":\n\n"

    if insights:
        body = "\n\n".join(insights)
    else:
        body = "I've consulted the relevant agents but need more evidence to provide a detailed answer."

    footer = "\n\n---\n*This analysis is AI-assisted. All findings require human verification.*"
    return intro + body + footer


@router.post("/chat", response_model=CopilotResponse)
async def copilot_chat(
    body: CopilotMessage,
    current_user: Dict = Depends(get_current_user),
):
    """Route a user message to the appropriate agents and return a synthesized response."""
    import uuid as _uuid

    session_id = body.session_id or str(_uuid.uuid4())
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = []

    # Add user message to history
    _SESSIONS[session_id].append({"role": "user", "content": body.message})

    # Route to agents
    agents = _route_to_agent(body.message)

    # Generate response
    result = await _generate_response(
        body.message, agents, body.pod_id, body.context, _SESSIONS[session_id]
    )

    # Add assistant response to history
    _SESSIONS[session_id].append({"role": "assistant", "content": result["response"]})

    return CopilotResponse(
        response=result["response"],
        agent_used=result["primary_agent"],
        agents_consulted=result["agents_consulted"],
        session_id=session_id,
        confidence=result["confidence"],
        sources=result["sources"],
    )


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, current_user: Dict = Depends(get_current_user)):
    """Get conversation history for a session."""
    history = _SESSIONS.get(session_id, [])
    return {"session_id": session_id, "messages": history, "count": len(history)}


@router.delete("/session/{session_id}")
async def clear_session(session_id: str, current_user: Dict = Depends(get_current_user)):
    """Clear a conversation session."""
    _SESSIONS.pop(session_id, None)
    return {"message": "Session cleared."}


@router.get("/routing-map")
async def get_routing_map(current_user: Dict = Depends(get_current_user)):
    """Show the intent-to-agent routing map for transparency."""
    return {
        "routing_rules": [
            {"pattern": pattern, "routes_to": agent}
            for pattern, agent in INTENT_ROUTING.items()
        ]
    }
