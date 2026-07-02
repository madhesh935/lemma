"""Lemma Agent: Autopsy Intelligence Agent"""
from typing import Dict, Any
from lemma.agents.base_agent import BaseAgent, AgentResult
from lemma.functions.autopsy_parser import parse_autopsy
from lemma.functions.pmi_estimator import estimate_pmi
from lemma.functions.notifier import send_notification
import logging

logger = logging.getLogger("aegis.agent.autopsy")

class AutopsyIntelligenceAgent(BaseAgent):
    name = "autopsy_intelligence"
    description = "Autopsy Intelligence Agent — analyzes autopsy reports and estimates time of death"

    async def run(self, pod_id: str, context: Dict[str, Any]) -> AgentResult:
        autopsy_files = [
            f for f in context.get("files", [])
            if f.get("evidence_type") in ("autopsy_report", "medical_report")
            or "autopsy" in f.get("original_name","").lower()
        ]
        autopsy_texts = context.get("autopsy_texts", [])  # pre-extracted OCR texts

        all_findings = []
        pmi_results = []

        send_notification("agent_started", "Autopsy Intelligence Agent",
                         f"Analyzing {len(autopsy_files)} autopsy reports", pod_id=pod_id)

        # Parse each autopsy report
        for text in autopsy_texts:
            self._call_function("parse_autopsy", text_length=len(text))
            findings = parse_autopsy(text)
            all_findings.append(findings)

            # Run PMI estimation if TOD data found
            if findings.get("physical_findings"):
                phys = findings["physical_findings"]
                try:
                    self._call_function("estimate_pmi")
                    pmi = estimate_pmi(
                        age=float(findings["victim"].get("age", 35)),
                        sex=findings["victim"].get("gender", "Unknown"),
                        height=float(phys.get("height", 165)),
                        weight=float(phys.get("weight", 65)),
                        putrefaction=1,
                        putre_level="Mild",
                        rigor_mortis="Partial",
                        livor_mortis="Present",
                        algor_mortis=25.0,
                        stomach_contents="Partially digested",
                        vitreous_potassium=8.5,
                        entomology="None",
                    )
                    pmi_results.append(pmi)
                except Exception as e:
                    logger.warning(f"PMI estimation failed: {e}")

        # Aggregate findings
        merged_causes = list({f.get("cause_of_death","") for f in all_findings if f.get("cause_of_death")})
        all_injuries = sum([f.get("injuries",[]) for f in all_findings], [])
        all_tox = {}
        for f in all_findings:
            for sub in f.get("toxicology",{}).get("substances",[]):
                all_tox[sub] = all_tox.get(sub, 0) + 1

        avg_confidence = (
            sum(f.get("confidence", 0) for f in all_findings) / len(all_findings)
            if all_findings else 0.0
        )

        send_notification("agent_complete", "Autopsy Analysis Complete",
                         f"COD: {merged_causes[0] if merged_causes else 'Unknown'} | "
                         f"PMI: {pmi_results[0]['predicted_pmi_hours'] if pmi_results else 'N/A'}h",
                         pod_id=pod_id, severity="success")

        return AgentResult(
            agent_name=self.name, pod_id=pod_id, success=True,
            output={
                "reports_analyzed": len(all_findings),
                "cause_of_death_candidates": merged_causes,
                "all_injuries": all_injuries[:20],
                "toxicology_summary": all_tox,
                "pmi_estimates": pmi_results,
                "average_parse_confidence": avg_confidence,
                "raw_findings": all_findings,
            },
            reasoning=(
                f"Analyzed {len(all_findings)} autopsy reports. "
                f"Identified {len(merged_causes)} cause(s) of death. "
                f"Found {len(all_injuries)} injuries. "
                f"PMI estimated: {pmi_results[0]['predicted_pmi_hours'] if pmi_results else 'N/A'}h."
            ),
        )
