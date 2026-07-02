"""AEGIS-OS Lemma Functions package — 15 independently callable forensic functions."""
from lemma.functions.ocr import run_ocr
from lemma.functions.entity_extraction import extract_entities
from lemma.functions.autopsy_parser import parse_autopsy
from lemma.functions.pmi_estimator import estimate_pmi
from lemma.functions.metadata_extractor import extract_metadata
from lemma.functions.gps_parser import parse_gps
from lemma.functions.timeline_builder import build_timeline
from lemma.functions.graph_builder import build_graph_updates
from lemma.functions.evidence_correlator import correlate_evidence
from lemma.functions.risk_scorer import calculate_risk_score
from lemma.functions.hypothesis_generator import generate_hypotheses
from lemma.functions.report_generator import generate_report
from lemma.functions.heatmap_generator import generate_heatmap
from lemma.functions.movement_reconstructor import reconstruct_movement
from lemma.functions.notifier import send_notification

__all__ = [
    "run_ocr", "extract_entities", "parse_autopsy", "estimate_pmi",
    "extract_metadata", "parse_gps", "build_timeline", "build_graph_updates",
    "correlate_evidence", "calculate_risk_score", "generate_hypotheses",
    "generate_report", "generate_heatmap", "reconstruct_movement", "send_notification",
]
