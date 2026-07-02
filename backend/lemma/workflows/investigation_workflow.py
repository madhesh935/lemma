"""
AEGIS-OS Lemma SDK — Investigation Workflow
=============================================
A 12-step durable forensic investigation workflow.

Steps:
  1.  pod_created          → Initialize pod state
  2.  evidence_uploaded    → Wait for file upload trigger
  3.  intake_running       → EvidenceIntakeAgent processing
  4.  intake_complete      → Files stored, structured
  5.  autopsy_analysis     → AutopsyIntelligenceAgent
  6.  digital_correlation  → DigitalCorrelationAgent
  7.  graph_update         → KnowledgeGraphAgent
  8.  timeline_build       → TimelineReconstructionAgent
  9.  risk_assessment      → RiskAssessmentAgent
  10. hypothesis_gen       → HypothesisAgent
  11. investigator_review  → ⚠️  HUMAN CHECKPOINT — pauses here
  12. report_generation    → ReportAgent (requires approval)
  13. case_closed          → Archive pod

Triggers: POST /workflows/start
Human gate: POST /workflows/{pod_id}/approve
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from lemma.agents.evidence_intake import EvidenceIntakeAgent
from lemma.agents.autopsy_intelligence import AutopsyIntelligenceAgent
from lemma.agents.digital_correlation import DigitalCorrelationAgent
from lemma.agents.timeline_reconstruction import TimelineReconstructionAgent
from lemma.agents.knowledge_graph import KnowledgeGraphAgent
from lemma.agents.hypothesis import HypothesisAgent
from lemma.agents.risk_assessment import RiskAssessmentAgent
from lemma.agents.report import ReportAgent
from lemma.functions.notifier import send_notification

logger = logging.getLogger("aegis.lemma.workflow")


WORKFLOW_STEPS = [
    "pod_created",
    "evidence_uploaded",
    "intake_running",
    "intake_complete",
    "autopsy_analysis",
    "digital_correlation",
    "graph_update",
    "timeline_build",
    "risk_assessment",
    "hypothesis_gen",
    "investigator_review",   # ← HUMAN CHECKPOINT
    "report_generation",
    "case_closed",
]


class WorkflowStepResult:
    def __init__(self, step: str, success: bool, data: Dict = None, error: str = None):
        self.step = step
        self.success = success
        self.data = data or {}
        self.error = error
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict:
        return {
            "step": self.step,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "timestamp": self.timestamp,
        }


class InvestigationWorkflow:
    """
    Lemma Investigation Workflow — orchestrates all 8 agents in sequence.
    Pauses at the human review checkpoint.
    Persists state to the workflow_states table.
    """

    def __init__(self, pod_id: str, llm_client=None):
        self.pod_id = pod_id
        self.llm = llm_client
        self.step_history: List[Dict] = []
        self.current_step: str = "pod_created"
        self.is_paused: bool = False
        self.context: Dict[str, Any] = {}

        # Initialize all agents
        self.agents = {
            "evidence_intake": EvidenceIntakeAgent(llm_client),
            "autopsy_intelligence": AutopsyIntelligenceAgent(llm_client),
            "digital_correlation": DigitalCorrelationAgent(llm_client),
            "timeline_reconstruction": TimelineReconstructionAgent(llm_client),
            "knowledge_graph": KnowledgeGraphAgent(llm_client),
            "hypothesis": HypothesisAgent(llm_client),
            "risk_assessment": RiskAssessmentAgent(llm_client),
            "report": ReportAgent(llm_client),
        }

    async def start(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start the investigation workflow.
        Runs all steps up to the human checkpoint.
        """
        self.context = initial_context.copy()
        logger.info(f"Workflow started for pod {self.pod_id}")

        send_notification(
            "workflow_started", "Investigation Workflow Started",
            f"Running automated analysis pipeline for pod {self.pod_id}",
            pod_id=self.pod_id, severity="info"
        )

        # Step 1: Intake
        await self._run_step("intake_running", self._step_intake)

        # Step 2: Autopsy Analysis
        await self._run_step("autopsy_analysis", self._step_autopsy)

        # Step 3: Digital Correlation
        await self._run_step("digital_correlation", self._step_digital_correlation)

        # Step 4: Knowledge Graph
        await self._run_step("graph_update", self._step_knowledge_graph)

        # Step 5: Timeline
        await self._run_step("timeline_build", self._step_timeline)

        # Step 6: Risk Assessment
        await self._run_step("risk_assessment", self._step_risk)

        # Step 7: Hypothesis Generation
        await self._run_step("hypothesis_gen", self._step_hypothesis)

        # Step 8: HUMAN CHECKPOINT ─────────────────────────────────────────
        self.current_step = "investigator_review"
        self.is_paused = True
        send_notification(
            "human_review_required",
            "⚠️ Investigator Review Required",
            "Automated analysis complete. Please review findings and approve before report generation.",
            pod_id=self.pod_id,
            severity="warning"
        )
        logger.info(f"Workflow paused at investigator_review for pod {self.pod_id}")

        return {
            "status": "paused_for_review",
            "current_step": self.current_step,
            "step_history": self.step_history,
            "context_summary": self._context_summary(),
        }

    async def approve_and_generate_report(self, approved_by: str, report_type: str = "investigator") -> Dict:
        """
        Called after human approval. Generates the final report.
        """
        if not self.is_paused:
            return {"error": "Workflow not at review checkpoint."}

        send_notification(
            "workflow_approved", "Investigation Approved",
            f"Approved by {approved_by}. Generating {report_type} report.",
            pod_id=self.pod_id, severity="info"
        )

        self.is_paused = False
        self.context["report_type"] = report_type
        self.context["approved_by"] = approved_by

        # Step 9: Report Generation
        await self._run_step("report_generation", self._step_report)

        # Step 10: Close
        self.current_step = "case_closed"
        send_notification(
            "case_closed", "Investigation Workflow Complete",
            "All steps complete. Case ready for archiving.",
            pod_id=self.pod_id, severity="success"
        )

        return {
            "status": "completed",
            "current_step": "case_closed",
            "step_history": self.step_history,
            "report": self.context.get("generated_report"),
        }

    # ─── Step Implementations ─────────────────────────────────────────────────

    async def _step_intake(self) -> WorkflowStepResult:
        result = await self.agents["evidence_intake"].invoke(self.pod_id, self.context)
        if result.success:
            self.context["intake_results"] = result.output
            # Store processed evidence for downstream agents
            self.context["processed_evidence"] = result.output.get("processed", [])
        return WorkflowStepResult("intake_running", result.success, result.output, result.error)

    async def _step_autopsy(self) -> WorkflowStepResult:
        # Extract autopsy texts from processed evidence
        autopsy_texts = []
        for item in self.context.get("intake_results", {}).get("processed", []):
            if item.get("ai_classification") in ("autopsy_report", "document_pdf"):
                text = item.get("extracted_text", "")
                if text:
                    autopsy_texts.append(text)

        self.context["autopsy_texts"] = autopsy_texts
        result = await self.agents["autopsy_intelligence"].invoke(self.pod_id, self.context)
        if result.success:
            self.context["autopsy_findings"] = result.output
        return WorkflowStepResult("autopsy_analysis", result.success, result.output, result.error)

    async def _step_digital_correlation(self) -> WorkflowStepResult:
        result = await self.agents["digital_correlation"].invoke(self.pod_id, self.context)
        if result.success:
            self.context["correlations"] = result.output
            self.context["movement"] = result.output.get("movement", {})
        return WorkflowStepResult("digital_correlation", result.success, result.output, result.error)

    async def _step_knowledge_graph(self) -> WorkflowStepResult:
        result = await self.agents["knowledge_graph"].invoke(self.pod_id, self.context)
        if result.success:
            self.context["graph_updates"] = result.output
        return WorkflowStepResult("graph_update", result.success, result.output, result.error)

    async def _step_timeline(self) -> WorkflowStepResult:
        result = await self.agents["timeline_reconstruction"].invoke(self.pod_id, self.context)
        if result.success:
            self.context["timeline"] = result.output.get("events", [])
            self.context["timeline_full"] = result.output
        return WorkflowStepResult("timeline_build", result.success, result.output, result.error)

    async def _step_risk(self) -> WorkflowStepResult:
        result = await self.agents["risk_assessment"].invoke(self.pod_id, self.context)
        if result.success:
            self.context["risk_score"] = result.output
        return WorkflowStepResult("risk_assessment", result.success, result.output, result.error)

    async def _step_hypothesis(self) -> WorkflowStepResult:
        result = await self.agents["hypothesis"].invoke(self.pod_id, self.context)
        if result.success:
            self.context["hypotheses"] = result.output.get("hypotheses", [])
        return WorkflowStepResult("hypothesis_gen", result.success, result.output, result.error)

    async def _step_report(self) -> WorkflowStepResult:
        result = await self.agents["report"].invoke(self.pod_id, self.context)
        if result.success:
            self.context["generated_report"] = result.output
        return WorkflowStepResult("report_generation", result.success, result.output, result.error)

    # ─── Utilities ────────────────────────────────────────────────────────────

    async def _run_step(self, step_name: str, step_fn) -> None:
        self.current_step = step_name
        logger.info(f"[Workflow {self.pod_id}] Running step: {step_name}")
        try:
            result = await step_fn()
            self.step_history.append(result.to_dict())
        except Exception as e:
            logger.error(f"Step {step_name} failed: {e}")
            self.step_history.append(WorkflowStepResult(step_name, False, error=str(e)).to_dict())

    def _context_summary(self) -> Dict:
        return {
            "files_processed": len(self.context.get("files", [])),
            "evidence_items": len(self.context.get("evidence", [])),
            "timeline_events": len(self.context.get("timeline", [])),
            "hypotheses": len(self.context.get("hypotheses", [])),
            "risk_score": self.context.get("risk_score", {}).get("overall_score"),
        }

    def get_state(self) -> Dict:
        return {
            "pod_id": self.pod_id,
            "current_step": self.current_step,
            "is_paused": self.is_paused,
            "step_history": self.step_history,
            "progress_pct": round(
                (WORKFLOW_STEPS.index(self.current_step) / len(WORKFLOW_STEPS)) * 100
                if self.current_step in WORKFLOW_STEPS else 0
            ),
        }
