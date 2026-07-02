"""Lemma Agent: Timeline Reconstruction Agent"""
from typing import Dict, Any, List
from lemma.agents.base_agent import BaseAgent, AgentResult
from lemma.functions.timeline_builder import build_timeline
from lemma.functions.notifier import send_notification

class TimelineReconstructionAgent(BaseAgent):
    name = "timeline_reconstruction"
    description = "Timeline Reconstruction Agent — builds chronological event timeline and resolves conflicts"

    async def run(self, pod_id: str, context: Dict[str, Any]) -> AgentResult:
        raw_events: List[Dict] = context.get("raw_events", [])
        evidence = context.get("evidence", [])

        send_notification("agent_started", "Timeline Agent", "Reconstructing investigation timeline", pod_id=pod_id)

        # Enrich events from evidence
        ev_events = []
        for ev in evidence:
            if ev.get("collected_at") or ev.get("uploaded_at"):
                ev_events.append({
                    "timestamp": ev.get("collected_at") or ev.get("uploaded_at"),
                    "type": ev.get("evidence_type", "evidence"),
                    "title": f"Evidence Collected: {ev.get('name','?')}",
                    "description": ev.get("ai_summary",""),
                    "source_evidence_id": ev.get("id"),
                    "confidence": 0.9,
                })

        all_events = raw_events + ev_events
        self._call_function("build_timeline", event_count=len(all_events))
        timeline = build_timeline(all_events)

        send_notification(
            "agent_complete", "Timeline Reconstructed",
            f"{len(timeline.get('events',[]))} events | {len(timeline.get('conflicts',[]))} conflicts | "
            f"Span: {timeline.get('span_hours',0):.1f}h",
            pod_id=pod_id, severity="success"
        )

        return AgentResult(
            agent_name=self.name, pod_id=pod_id, success=True,
            output=timeline,
            reasoning=(
                f"Built timeline from {len(all_events)} events. "
                f"Detected {len(timeline.get('conflicts',[]))} conflicts and "
                f"{len(timeline.get('gaps',[]))} gaps. "
                f"Total span: {timeline.get('span_hours',0):.1f} hours."
            ),
        )
