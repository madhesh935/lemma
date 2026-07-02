"""Lemma Agent: Report Agent"""
from typing import Dict, Any
from lemma.agents.base_agent import BaseAgent, AgentResult
from lemma.functions.report_generator import generate_report
from lemma.functions.notifier import send_notification

class ReportAgent(BaseAgent):
    name = "report"
    description = "Report Agent — generates executive, investigator, court, and evidence index reports"

    async def run(self, pod_id: str, context: Dict[str, Any]) -> AgentResult:
        report_type = context.get("report_type", "investigator")
        case = context.get("case", {})
        evidence = context.get("evidence", [])
        timeline = context.get("timeline", [])
        hypotheses = context.get("hypotheses", [])
        risk = context.get("risk_score", {})
        persons = context.get("persons", [])

        send_notification("agent_started", "Report Agent",
                         f"Generating {report_type} report", pod_id=pod_id)

        self._call_function("generate_report", report_type=report_type)
        report = generate_report(
            report_type=report_type,
            case=case, evidence=evidence, timeline=timeline,
            hypotheses=hypotheses, risk_score=risk, persons=persons,
        )

        send_notification(
            "report_ready", "Report Ready for Review",
            f"{report_type.upper()} report generated. Awaiting investigator approval.",
            pod_id=pod_id, severity="info"
        )

        return AgentResult(
            agent_name=self.name, pod_id=pod_id, success=True,
            output=report,
            reasoning=(
                f"Generated {report_type} report for pod {pod_id}. "
                f"Status: DRAFT — requires human approval before finalization. "
                f"Content: {len(report.get('content_markdown',''))} chars."
            ),
        )
