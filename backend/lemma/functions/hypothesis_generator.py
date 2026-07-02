"""
Lemma Function: Hypothesis Generator
======================================
Generates multiple investigative hypotheses from evidence + timeline.
IMPORTANT: Never declares guilt. Assigns confidence. Suggests next steps.
"""
from typing import List, Dict, Any
import logging
logger = logging.getLogger("aegis.fn.hypothesis")

def generate_hypotheses(
    case: Dict[str, Any],
    evidence: List[Dict],
    timeline: List[Dict],
    persons: List[Dict],
    llm_client=None,
) -> List[Dict[str, Any]]:
    """
    Generate structured investigative hypotheses.
    Uses LLM if available, falls back to rule-based generation.
    """
    if llm_client:
        return _llm_hypotheses(case, evidence, timeline, persons, llm_client)
    return _rule_based_hypotheses(case, evidence, timeline, persons)


def _rule_based_hypotheses(case, evidence, timeline, persons) -> List[Dict]:
    hypotheses = []
    ev_types = {e.get("type") for e in evidence}
    suspects = [p for p in persons if p.get("role") == "suspect"]
    victims = [p for p in persons if p.get("role") == "victim"]

    # H1: Primary suspect hypothesis
    if suspects:
        s = suspects[0]
        hyp = {
            "hypothesis_number": 1,
            "title": f"Primary Suspect Involvement — {s.get('name','Unknown')}",
            "description": (
                f"Based on available evidence, {s.get('name','the primary suspect')} may be linked "
                f"to the incident. This hypothesis requires further corroboration."
            ),
            "confidence_score": 0.45,
            "supporting_evidence_ids": [e.get("id") for e in evidence[:3] if e.get("id")],
            "contradicting_evidence_ids": [],
            "additional_evidence_needed": ["CCTV footage", "alibi verification", "financial records"],
            "reasoning": "Suspect identified in proximity. Digital trace analysis pending.",
        }
        hypotheses.append(hyp)

    # H2: Unknown perpetrator
    hypotheses.append({
        "hypothesis_number": len(hypotheses) + 1,
        "title": "Unknown Third Party Involvement",
        "description": (
            "Evidence may point to an unidentified individual not yet in the person registry. "
            "Surveillance footage and CDR analysis may reveal additional persons of interest."
        ),
        "confidence_score": 0.35,
        "supporting_evidence_ids": [e.get("id") for e in evidence if e.get("type") == "cctv_video"],
        "contradicting_evidence_ids": [],
        "additional_evidence_needed": ["Expanded CDR radius", "area CCTV review", "witness canvassing"],
        "reasoning": "Timeline gaps suggest possible unaccounted actors.",
    })

    # H3: Accidental / natural causes (always include as alternative)
    if "autopsy_report" in ev_types:
        hypotheses.append({
            "hypothesis_number": len(hypotheses) + 1,
            "title": "Accidental or Natural Cause",
            "description": (
                "Autopsy findings may be consistent with accidental or natural death. "
                "Full toxicology and scene reconstruction required to rule this out."
            ),
            "confidence_score": 0.20,
            "supporting_evidence_ids": [e.get("id") for e in evidence if e.get("type") == "autopsy_report"],
            "contradicting_evidence_ids": [],
            "additional_evidence_needed": ["Complete toxicology screen", "scene photographs"],
            "reasoning": "Alternative hypothesis maintained to avoid premature conclusions.",
        })

    return hypotheses


def _llm_hypotheses(case, evidence, timeline, persons, llm_client) -> List[Dict]:
    """LLM-powered hypothesis generation."""
    ev_summary = "\n".join([
        f"- {e.get('name','?')} ({e.get('type','?')}): {e.get('ai_summary','')[:100]}"
        for e in evidence[:10]
    ])
    timeline_summary = "\n".join([
        f"- [{ev.get('timestamp_iso','?')[:16]}] {ev.get('title','?')}"
        for ev in timeline[:8]
    ])
    person_summary = "\n".join([
        f"- {p.get('name','?')} ({p.get('role','?')})"
        for p in persons[:5]
    ])

    prompt = f"""You are a forensic intelligence assistant for case: {case.get('name','?')}.

Evidence:
{ev_summary}

Timeline:
{timeline_summary}

Persons:
{person_summary}

Generate 3 distinct investigative hypotheses. For each hypothesis:
1. Give it a clear title
2. Describe what may have happened (do NOT declare guilt)
3. Rate confidence 0.0-1.0
4. List supporting evidence
5. List additional evidence needed

IMPORTANT: Never state someone is guilty. Use language like "may be linked", "possibly involved", "warrants further investigation".

Respond in JSON: list of objects with keys: title, description, confidence_score (float), reasoning, additional_evidence_needed (list)"""

    try:
        response = llm_client.generate(prompt)
        import json
        raw = response.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        items = json.loads(raw)
        return [
            {
                "hypothesis_number": i + 1,
                "title": item.get("title",""),
                "description": item.get("description",""),
                "confidence_score": float(item.get("confidence_score", 0.3)),
                "supporting_evidence_ids": [],
                "contradicting_evidence_ids": [],
                "additional_evidence_needed": item.get("additional_evidence_needed", []),
                "reasoning": item.get("reasoning",""),
            }
            for i, item in enumerate(items[:5])
        ]
    except Exception as e:
        logger.warning(f"LLM hypothesis generation failed: {e}. Using rule-based.")
        return _rule_based_hypotheses(case, evidence, timeline, persons)
