"""
Lemma Function: Entity Extraction
==================================
Extracts named entities (persons, places, dates, phone numbers, amounts)
from raw text using NLP + LLM fallback.
"""
from __future__ import annotations
import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("aegis.fn.entity_extraction")


def extract_entities(text: str, context: str = "forensic") -> Dict[str, Any]:
    """
    Extract forensic entities from unstructured text.

    Returns:
        {
          "persons": [{"name": str, "role": str, "mentions": int}],
          "locations": [{"name": str, "type": str}],
          "dates_times": [{"raw": str, "iso": str}],
          "phone_numbers": [str],
          "financial": [{"amount": float, "currency": str, "context": str}],
          "vehicles": [{"plate": str, "description": str}],
          "devices": [{"type": str, "identifier": str}],
          "raw_entities": dict,
          "method": str,
        }
    """
    result = {
        "persons": [],
        "locations": [],
        "dates_times": [],
        "phone_numbers": [],
        "financial": [],
        "vehicles": [],
        "devices": [],
        "raw_entities": {},
        "method": "regex",
    }

    if not text or not text.strip():
        return result

    # Try spaCy NLP first
    spacy_result = _try_spacy(text, result)
    if spacy_result:
        result = spacy_result
        result["method"] = "spacy"

    # Always run regex extraction (catches forensic-specific patterns)
    result = _regex_extraction(text, result)

    logger.info(
        f"Entity extraction: {len(result['persons'])} persons, "
        f"{len(result['locations'])} locations, "
        f"{len(result['phone_numbers'])} phones"
    )
    return result


def _try_spacy(text: str, result: dict) -> Optional[dict]:
    try:
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            return None

        doc = nlp(text[:100_000])  # Cap at 100k chars
        persons = {}
        locations = []
        dates = []

        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text.strip()
                persons[name] = persons.get(name, 0) + 1
            elif ent.label_ in ("GPE", "LOC", "FAC"):
                locations.append({"name": ent.text.strip(), "type": ent.label_.lower()})
            elif ent.label_ in ("DATE", "TIME"):
                dates.append({"raw": ent.text.strip(), "iso": ""})

        result["persons"] = [{"name": n, "role": "unknown", "mentions": c} for n, c in persons.items()]
        result["locations"] = locations
        result["dates_times"] = dates
        result["raw_entities"] = {ent.text: ent.label_ for ent in doc.ents}
        return result
    except ImportError:
        return None


def _regex_extraction(text: str, result: dict) -> dict:
    """Pattern-based extraction for forensic-specific entities."""

    # Phone numbers (Indian + international)
    phone_patterns = [
        r"\b(?:\+91|91)?[6-9]\d{9}\b",      # Indian mobile
        r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b",  # US format
        r"\b\+\d{1,3}\s?\d{6,14}\b",          # International
    ]
    phones = set()
    for p in phone_patterns:
        phones.update(re.findall(p, text))
    result["phone_numbers"] = list(phones)

    # Financial amounts
    financial_pattern = r"(?:₹|Rs\.?|INR|USD|\$)\s?[\d,]+(?:\.\d{2})?"
    for match in re.finditer(financial_pattern, text, re.IGNORECASE):
        raw = match.group()
        amount_str = re.sub(r"[₹$Rs\.INRUSDa-zA-Z,\s]", "", raw)
        try:
            amount = float(amount_str)
            start = max(0, match.start() - 40)
            end = min(len(text), match.end() + 40)
            result["financial"].append({
                "amount": amount,
                "currency": "INR" if "₹" in raw or "Rs" in raw else "USD",
                "context": text[start:end].strip(),
            })
        except ValueError:
            pass

    # Vehicle registration plates (Indian format)
    plate_pattern = r"\b[A-Z]{2}\s?\d{1,2}\s?[A-Z]{1,3}\s?\d{1,4}\b"
    for match in re.finditer(plate_pattern, text):
        result["vehicles"].append({"plate": match.group().strip(), "description": ""})

    # Device identifiers (IMEI, MAC, IP)
    imei_pattern = r"\b\d{15,17}\b"
    mac_pattern = r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b"
    ip_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"

    for match in re.finditer(imei_pattern, text):
        result["devices"].append({"type": "imei", "identifier": match.group()})
    for match in re.finditer(mac_pattern, text):
        result["devices"].append({"type": "mac_address", "identifier": match.group()})
    for match in re.finditer(ip_pattern, text):
        result["devices"].append({"type": "ip_address", "identifier": match.group()})

    # Dates (additional regex for any spaCy misses)
    date_patterns = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2})?)?\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b",
    ]
    existing_dates = {d["raw"] for d in result["dates_times"]}
    for pattern in date_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            raw = match.group().strip()
            if raw not in existing_dates:
                result["dates_times"].append({"raw": raw, "iso": ""})
                existing_dates.add(raw)

    return result
