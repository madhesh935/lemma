"""AEGIS-OS Lemma Agents package — 8 specialized forensic AI agents."""
from lemma.agents.base_agent import BaseAgent
from lemma.agents.evidence_intake import EvidenceIntakeAgent
from lemma.agents.autopsy_intelligence import AutopsyIntelligenceAgent
from lemma.agents.digital_correlation import DigitalCorrelationAgent
from lemma.agents.timeline_reconstruction import TimelineReconstructionAgent
from lemma.agents.knowledge_graph import KnowledgeGraphAgent
from lemma.agents.hypothesis import HypothesisAgent
from lemma.agents.risk_assessment import RiskAssessmentAgent
from lemma.agents.report import ReportAgent

AGENT_REGISTRY = {
    "evidence_intake": EvidenceIntakeAgent,
    "autopsy_intelligence": AutopsyIntelligenceAgent,
    "digital_correlation": DigitalCorrelationAgent,
    "timeline_reconstruction": TimelineReconstructionAgent,
    "knowledge_graph": KnowledgeGraphAgent,
    "hypothesis": HypothesisAgent,
    "risk_assessment": RiskAssessmentAgent,
    "report": ReportAgent,
}

def get_agent(name: str) -> type:
    agent_cls = AGENT_REGISTRY.get(name)
    if not agent_cls:
        raise ValueError(f"Unknown agent: {name}. Available: {list(AGENT_REGISTRY.keys())}")
    return agent_cls

__all__ = [
    "BaseAgent", "EvidenceIntakeAgent", "AutopsyIntelligenceAgent",
    "DigitalCorrelationAgent", "TimelineReconstructionAgent",
    "KnowledgeGraphAgent", "HypothesisAgent", "RiskAssessmentAgent",
    "ReportAgent", "AGENT_REGISTRY", "get_agent",
]
