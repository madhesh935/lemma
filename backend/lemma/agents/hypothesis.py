"""Lemma Agent: Hypothesis Agent"""
from typing import Dict, Any
from lemma.agents.base_agent import BaseAgent, AgentResult
from lemma.functions.hypothesis_generator import generate_hypotheses
from lemma.functions.notifier import send_notification

class HypothesisAgent(BaseAgent):
    name = "hypothesis"
    description = "Hypothesis Agent — generates multiple investigative hypotheses with evidence backing"

    async def run(self, pod_id: str, context: Dict[str, Any]) -> AgentResult:
        case = context.get("case", {})
        evidence = context.get("evidence", [])
        timeline = context.get("timeline", [])
        persons = context.get("persons", [])

        send_notification("agent_started", "Hypothesis Agent",
                         "Generating investigative hypotheses", pod_id=pod_id)

        self._call_function("generate_hypotheses", evidence_count=len(evidence))
        hypotheses = generate_hypotheses(
            case=case, evidence=evidence, timeline=timeline,
            persons=persons, llm_client=self.llm
        )

        top = sorted(hypotheses, key=lambda h: h.get("confidence_score", 0), reverse=True)
        top_title = top[0]["title"] if top else "None"

        send_notification(
            "agent_complete", "Hypotheses Generated",
            f"{len(hypotheses)} hypotheses | Leading: {top_title[:60]}",
            pod_id=pod_id, severity="success"
        )

        return AgentResult(
            agent_name=self.name, pod_id=pod_id, success=True,
            output={"hypotheses": hypotheses, "count": len(hypotheses),
                    "leading_hypothesis": top[0] if top else None},
            reasoning=(
                f"Generated {len(hypotheses)} investigative hypotheses. "
                f"Leading hypothesis: '{top_title}' "
                f"({top[0].get('confidence_score',0):.0%} confidence)."
            ),
        )
