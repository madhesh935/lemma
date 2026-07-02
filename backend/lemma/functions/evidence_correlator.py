"""Lemma Function: Evidence Correlator"""
from typing import List, Dict, Any
import logging
logger = logging.getLogger("aegis.fn.correlator")

def correlate_evidence(evidence_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Identify correlations between evidence items across GPS, CDR, CCTV, witness, financial.
    Returns a correlation matrix and high-confidence links.
    """
    correlations = []
    high_confidence = []
    
    for i, a in enumerate(evidence_list):
        for j, b in enumerate(evidence_list):
            if i >= j:
                continue
            score = 0.0
            reasons = []
            
            # Temporal correlation
            if a.get("timestamp") and b.get("timestamp"):
                try:
                    from datetime import datetime
                    ta = datetime.fromisoformat(str(a["timestamp"]).replace("Z",""))
                    tb = datetime.fromisoformat(str(b["timestamp"]).replace("Z",""))
                    delta = abs((ta - tb).total_seconds())
                    if delta < 1800:  # within 30 mins
                        score += 0.3
                        reasons.append(f"Within {int(delta/60)} min of each other")
                except Exception:
                    pass

            # Spatial correlation
            if a.get("lat") and b.get("lat"):
                dlat = abs(a["lat"] - b["lat"])
                dlng = abs(a.get("lng",0) - b.get("lng",0))
                if dlat < 0.01 and dlng < 0.01:
                    score += 0.3
                    reasons.append("Same geographic area")

            # Person overlap
            a_persons = set(a.get("persons") or [])
            b_persons = set(b.get("persons") or [])
            overlap = a_persons & b_persons
            if overlap:
                score += 0.4
                reasons.append(f"Shared persons: {', '.join(list(overlap)[:3])}")

            if score > 0:
                link = {
                    "evidence_a": a.get("id") or a.get("name"),
                    "evidence_b": b.get("id") or b.get("name"),
                    "correlation_score": round(score, 2),
                    "reasons": reasons,
                }
                correlations.append(link)
                if score >= 0.6:
                    high_confidence.append(link)

    correlations.sort(key=lambda x: x["correlation_score"], reverse=True)
    return {
        "correlations": correlations[:50],
        "high_confidence_links": high_confidence,
        "total_pairs_analyzed": len(evidence_list) * (len(evidence_list) - 1) // 2,
    }
