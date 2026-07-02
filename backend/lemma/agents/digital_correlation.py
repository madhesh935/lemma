"""Lemma Agent: Digital Correlation Agent"""
from typing import Dict, Any
from lemma.agents.base_agent import BaseAgent, AgentResult
from lemma.functions.gps_parser import parse_gps
from lemma.functions.evidence_correlator import correlate_evidence
from lemma.functions.movement_reconstructor import reconstruct_movement
from lemma.functions.notifier import send_notification
import logging

logger = logging.getLogger("aegis.agent.digital_correlation")

class DigitalCorrelationAgent(BaseAgent):
    name = "digital_correlation"
    description = "Digital Correlation Agent — correlates GPS, CDR, CCTV, and phone metadata"

    async def run(self, pod_id: str, context: Dict[str, Any]) -> AgentResult:
        evidence = context.get("evidence", [])
        files = context.get("files", [])

        send_notification("agent_started", "Digital Correlation Agent",
                         "Correlating digital evidence sources", pod_id=pod_id)

        gps_waypoints = []
        cdr_records = []
        cctv_sightings = []

        # Parse GPS files
        for f in files:
            if f.get("evidence_type") == "gps_log" or ".gpx" in f.get("original_name","").lower():
                self._call_function("parse_gps", file_path=f.get("stored_path",""))
                try:
                    gps = parse_gps(file_path=f.get("stored_path",""))
                    gps_waypoints.extend(gps.get("waypoints",[]))
                except Exception as e:
                    logger.warning(f"GPS parse failed: {e}")

            if f.get("evidence_type") == "call_detail_record":
                cdr_records.append({"source_file": f.get("original_name")})

            if f.get("evidence_type") == "cctv_video":
                cctv_sightings.append({"camera_id": f.get("original_name")})

        # Correlate all evidence
        self._call_function("correlate_evidence", count=len(evidence))
        correlations = correlate_evidence(evidence)

        # Reconstruct movement
        self._call_function("reconstruct_movement")
        movement = reconstruct_movement(gps_waypoints, cdr_records, cctv_sightings)

        send_notification("agent_complete", "Digital Correlation Complete",
                         f"{len(correlations['high_confidence_links'])} high-confidence links found",
                         pod_id=pod_id, severity="success")

        return AgentResult(
            agent_name=self.name, pod_id=pod_id, success=True,
            output={
                "correlations": correlations,
                "movement": movement,
                "gps_waypoints": len(gps_waypoints),
                "cdr_records": len(cdr_records),
                "cctv_sightings": len(cctv_sightings),
                "high_confidence_links": correlations.get("high_confidence_links", []),
            },
            reasoning=(
                f"Correlated {len(evidence)} evidence items. "
                f"Found {len(correlations.get('high_confidence_links',[]))} high-confidence links. "
                f"Movement path: {movement.get('total_stops',0)} stops from "
                f"{', '.join(movement.get('sources_used',[]))} sources."
            ),
        )
