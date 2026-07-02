"""Lemma Function: Risk Scorer"""
from typing import Dict, Any, List
import logging
logger = logging.getLogger("aegis.fn.risk")

def calculate_risk_score(case: Dict[str, Any], evidence: List[Dict], hypotheses: List[Dict] = None) -> Dict[str, Any]:
    """
    Calculate a holistic risk/priority score for a forensic case (0-100).
    Factors: evidence volume, conflicts, timeline gaps, AI confidence, severity.
    """
    score = 0.0
    factors = {}
    anomalies = []
    inconsistencies = []

    # 1. Severity baseline
    severity_scores = {"critical": 40, "high": 30, "medium": 20, "low": 10}
    sev = case.get("severity", "medium")
    base = severity_scores.get(sev, 20)
    score += base
    factors["severity"] = base

    # 2. Evidence quantity
    ev_count = len(evidence)
    ev_score = min(20, ev_count * 2)
    score += ev_score
    factors["evidence_volume"] = ev_score

    # 3. Conflicting evidence
    conflicts = [e for e in evidence if e.get("is_conflicting")]
    if conflicts:
        conflict_score = min(15, len(conflicts) * 5)
        score += conflict_score
        factors["conflicts"] = conflict_score
        for c in conflicts:
            inconsistencies.append(f"Conflicting evidence: {c.get('name','?')}")

    # 4. Missing evidence types
    ev_types = {e.get("type") for e in evidence}
    expected = {"autopsy_report", "witness_statement", "gps_log"}
    missing = expected - ev_types
    if missing:
        score += len(missing) * 3
        factors["missing_evidence"] = len(missing) * 3
        for m in missing:
            anomalies.append({"type": "missing_evidence", "detail": f"No {m} uploaded"})

    # 5. Hypothesis confidence spread
    if hypotheses:
        max_conf = max((h.get("confidence_score", 0) for h in hypotheses), default=0)
        if max_conf < 0.4:
            score += 10
            anomalies.append({"type": "low_hypothesis_confidence", "detail": "Best hypothesis < 40% confidence"})
        factors["hypothesis_quality"] = max_conf * 10

    score = min(100, round(score, 1))

    # Urgency level
    if score >= 75:
        urgency = "critical"
    elif score >= 55:
        urgency = "high"
    elif score >= 35:
        urgency = "medium"
    else:
        urgency = "low"

    recommendations = []
    if "missing_evidence" in factors:
        recommendations.append("Upload missing evidence types: " + ", ".join(missing))
    if conflicts:
        recommendations.append("Resolve conflicting evidence before proceeding to report")
    if score >= 75:
        recommendations.append("Escalate to senior investigator immediately")

    return {
        "overall_score": score,
        "urgency_level": urgency,
        "factors": factors,
        "anomalies": anomalies,
        "inconsistencies": inconsistencies,
        "recommendations": recommendations,
    }
