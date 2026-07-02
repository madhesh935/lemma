"""Lemma Agent: Risk Assessment Agent"""
from typing import Dict, Any
from lemma.agents.base_agent import BaseAgent, AgentResult
from lemma.functions.risk_scorer import calculate_risk_score
from lemma.functions.notifier import send_notification

class RiskAssessmentAgent(BaseAgent):
    name = "risk_assessment"
    description = "Risk Assessment Agent — calculates case priority, detects anomalies, and generates urgency score"

    async def run(self, pod_id: str, context: Dict[str, Any]) -> AgentResult:
        case = context.get("case", {})
        evidence = context.get("evidence", [])
        hypotheses = context.get("hypotheses", [])

        send_notification("agent_started", "Risk Assessment Agent",
                         "Calculating case risk score", pod_id=pod_id)

        self._call_function("calculate_risk_score", evidence_count=len(evidence))
        risk = calculate_risk_score(case, evidence, hypotheses)

        send_notification(
            "agent_complete", "Risk Score Updated",
            f"Score: {risk['overall_score']}/100 | Urgency: {risk['urgency_level'].upper()}",
            pod_id=pod_id,
            severity="error" if risk["urgency_level"] == "critical" else
                     "warning" if risk["urgency_level"] == "high" else "success"
        )

        return AgentResult(
            agent_name=self.name, pod_id=pod_id, success=True,
            output=risk,
            reasoning=(
                f"Risk score: {risk['overall_score']}/100 ({risk['urgency_level']}). "
                f"Detected {len(risk.get('anomalies',[]))} anomalies. "
                f"Recommendations: {len(risk.get('recommendations',[]))}."
            ),
        )
