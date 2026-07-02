"""
Lemma Function: Autopsy Parser
================================
Extracts structured forensic findings from autopsy reports:
injuries, cause of death, toxicology, and time of death estimates.
"""
from __future__ import annotations
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("aegis.fn.autopsy_parser")


def parse_autopsy(text: str) -> Dict[str, Any]:
    """
    Parse an autopsy report text and return structured findings.

    Returns:
        {
          "victim": dict,
          "cause_of_death": str,
          "manner_of_death": str,
          "injuries": List[dict],
          "toxicology": dict,
          "time_of_death_window": dict,
          "physical_findings": dict,
          "confidence": float,
          "raw_sections": dict,
        }
    """
    result = {
        "victim": {},
        "cause_of_death": "",
        "manner_of_death": "",
        "injuries": [],
        "toxicology": {},
        "time_of_death_window": {},
        "physical_findings": {},
        "confidence": 0.0,
        "raw_sections": {},
    }

    if not text or len(text.strip()) < 50:
        return result

    text_clean = text.replace("\r\n", "\n").replace("\r", "\n")
    sections = _split_sections(text_clean)
    result["raw_sections"] = {k: v[:500] for k, v in sections.items()}  # truncate for storage

    # Parse each section
    result["victim"] = _parse_victim(sections.get("identification", text_clean[:500]))
    result["cause_of_death"] = _parse_cause_of_death(text_clean, sections)
    result["manner_of_death"] = _parse_manner_of_death(text_clean)
    result["injuries"] = _parse_injuries(sections.get("injuries", text_clean))
    result["toxicology"] = _parse_toxicology(sections.get("toxicology", ""))
    result["time_of_death_window"] = _parse_tod_window(text_clean)
    result["physical_findings"] = _parse_physical_findings(text_clean)
    result["confidence"] = _calculate_parse_confidence(result)

    logger.info(
        f"Autopsy parsed: COD='{result['cause_of_death']}', "
        f"{len(result['injuries'])} injuries, "
        f"confidence={result['confidence']:.0%}"
    )
    return result


def _split_sections(text: str) -> Dict[str, str]:
    """Split report into named sections."""
    sections: Dict[str, str] = {}
    section_headers = {
        "identification": r"(identification|personal details|decedent|name of deceased)",
        "injuries": r"(external examination|injuries|wounds|trauma|findings on body)",
        "toxicology": r"(toxicology|chemical analysis|blood alcohol|drug screen|poison)",
        "microscopy": r"(histology|microscopic|microscopy)",
        "opinion": r"(opinion|conclusion|cause of death|final diagnosis)",
        "radiological": r"(x-ray|radiological|CT scan|MRI)",
    }
    lines = text.split("\n")
    current = "general"
    buffer: List[str] = []

    for line in lines:
        matched = False
        for key, pattern in section_headers.items():
            if re.search(pattern, line, re.IGNORECASE):
                if buffer:
                    sections[current] = "\n".join(buffer)
                current = key
                buffer = [line]
                matched = True
                break
        if not matched:
            buffer.append(line)

    if buffer:
        sections[current] = "\n".join(buffer)
    return sections


def _parse_victim(text: str) -> Dict[str, str]:
    victim = {}
    name_match = re.search(r"(?:name|decedent|deceased)[:\s]+([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)", text, re.IGNORECASE)
    if name_match:
        victim["name"] = name_match.group(1).strip()
    age_match = re.search(r"(?:age|years)[:\s]+(\d{1,3})", text, re.IGNORECASE)
    if age_match:
        victim["age"] = age_match.group(1)
    gender_match = re.search(r"\b(male|female|man|woman|boy|girl)\b", text, re.IGNORECASE)
    if gender_match:
        victim["gender"] = gender_match.group(1).lower()
    return victim


def _parse_cause_of_death(text: str, sections: Dict) -> str:
    patterns = [
        r"cause of death[:\s]+([^\n\.]+)",
        r"died (?:due to|of|from)[:\s]+([^\n\.]+)",
        r"death (?:was caused|resulted) (?:by|from)[:\s]+([^\n\.]+)",
        r"COD[:\s]+([^\n\.]+)",
    ]
    search_text = sections.get("opinion", text)
    for p in patterns:
        m = re.search(p, search_text, re.IGNORECASE)
        if m:
            return m.group(1).strip()[:300]
    return "Undetermined from text"


def _parse_manner_of_death(text: str) -> str:
    patterns = [
        r"manner of death[:\s]+([^\n\.]+)",
        r"\b(homicide|suicide|accident|natural|undetermined)\b",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1).strip().capitalize()
    return "Unknown"


def _parse_injuries(text: str) -> List[Dict[str, str]]:
    injuries = []
    injury_keywords = [
        r"(?:laceration|contusion|abrasion|fracture|hemorrhage|bruising|"
        r"stab wound|gunshot|blunt force|cut|bruise|hematoma|edema)[^\n\.]{0,120}",
    ]
    for pattern in injury_keywords:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            desc = match.group().strip()
            if len(desc) > 10:
                # Try to extract location on body
                location_match = re.search(
                    r"(?:on|to|of|in)\s+(?:the\s+)?(\w+(?:\s+\w+)?)\s+(?:area|region|side|surface)?",
                    desc, re.IGNORECASE
                )
                injuries.append({
                    "description": desc[:200],
                    "location": location_match.group(1) if location_match else "unspecified",
                    "type": _classify_injury_type(desc),
                })
    return injuries[:20]  # Cap at 20


def _classify_injury_type(desc: str) -> str:
    desc_lower = desc.lower()
    if any(w in desc_lower for w in ["lacerat", "cut", "incis"]):
        return "laceration"
    if any(w in desc_lower for w in ["bruise", "contus", "hematom"]):
        return "blunt_force"
    if "stab" in desc_lower or "puncture" in desc_lower:
        return "stab"
    if "gunshot" in desc_lower or "bullet" in desc_lower:
        return "gunshot"
    if "fractur" in desc_lower:
        return "fracture"
    if "abras" in desc_lower:
        return "abrasion"
    return "other"


def _parse_toxicology(text: str) -> Dict[str, Any]:
    tox = {"substances": [], "blood_alcohol_level": None, "positive_findings": []}
    if not text:
        return tox

    bac_match = re.search(r"(?:blood alcohol|BAC|ethanol)[:\s]+(\d+\.?\d*)\s*(?:mg|g|%)", text, re.IGNORECASE)
    if bac_match:
        tox["blood_alcohol_level"] = float(bac_match.group(1))

    substance_patterns = [
        r"\b(cocaine|heroin|methamphetamine|fentanyl|morphine|benzodiazepine|"
        r"barbiturate|opioid|cannabis|THC|alcohol|poison|arsenic|cyanide)\b"
    ]
    found = set()
    for pattern in substance_patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            found.add(m.group(1).lower())
    tox["substances"] = list(found)

    positive_pattern = r"positive for ([^\n\.]+)"
    for m in re.finditer(positive_pattern, text, re.IGNORECASE):
        tox["positive_findings"].append(m.group(1).strip())

    return tox


def _parse_tod_window(text: str) -> Dict[str, Any]:
    tod = {"estimated_low": "", "estimated_high": "", "method": "", "confidence": 0.5}
    time_pattern = r"(?:time of death|died between|TOD)[:\s]+([^\n\.]{5,80})"
    m = re.search(time_pattern, text, re.IGNORECASE)
    if m:
        raw = m.group(1).strip()
        tod["raw"] = raw
        # Try to extract two times (range)
        times = re.findall(r"\d{1,2}[:\s]\d{2}\s?(?:AM|PM|hrs?)?", raw, re.IGNORECASE)
        if len(times) >= 2:
            tod["estimated_low"] = times[0]
            tod["estimated_high"] = times[1]
        elif len(times) == 1:
            tod["estimated_low"] = times[0]
        tod["confidence"] = 0.7

    methods = ["rigor mortis", "livor mortis", "algor mortis", "stomach contents", "entomology"]
    for method in methods:
        if method in text.lower():
            tod["method"] = method
            break

    return tod


def _parse_physical_findings(text: str) -> Dict[str, Any]:
    findings = {}
    height_m = re.search(r"(?:height|ht)[:\s]+([\d.]+)\s*(?:cm|m|feet|ft)", text, re.IGNORECASE)
    weight_m = re.search(r"(?:weight|wt)[:\s]+([\d.]+)\s*(?:kg|lbs?)", text, re.IGNORECASE)
    if height_m:
        findings["height"] = height_m.group(1)
    if weight_m:
        findings["weight"] = weight_m.group(1)
    return findings


def _calculate_parse_confidence(result: dict) -> float:
    score = 0.0
    if result["cause_of_death"] and result["cause_of_death"] != "Undetermined from text":
        score += 0.3
    if result["injuries"]:
        score += 0.2
    if result["victim"].get("name"):
        score += 0.2
    if result["toxicology"]["substances"] or result["toxicology"]["positive_findings"]:
        score += 0.15
    if result["time_of_death_window"].get("estimated_low"):
        score += 0.15
    return min(score, 1.0)
