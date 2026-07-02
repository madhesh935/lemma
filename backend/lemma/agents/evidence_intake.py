"""
Lemma Agent: Evidence Intake Agent
====================================
Responsibilities:
  - Read uploaded files from Pod Files
  - Extract metadata from each file
  - Run OCR on images and PDFs
  - Classify evidence type
  - Extract named entities
  - Store structured evidence records
"""
from __future__ import annotations
from typing import Dict, Any, List
import logging

from lemma.agents.base_agent import BaseAgent, AgentResult
from lemma.functions.ocr import run_ocr
from lemma.functions.entity_extraction import extract_entities
from lemma.functions.metadata_extractor import extract_metadata
from lemma.functions.notifier import send_notification

logger = logging.getLogger("aegis.agent.evidence_intake")


class EvidenceIntakeAgent(BaseAgent):
    name = "evidence_intake"
    description = "Evidence Intake Agent — classifies, OCRs, and structures uploaded forensic files"
    version = "1.0.0"

    async def run(self, pod_id: str, context: Dict[str, Any]) -> AgentResult:
        files: List[Dict] = context.get("files", [])
        processed = []
        errors = []

        send_notification(
            "agent_started", "Evidence Intake Agent", f"Processing {len(files)} files",
            pod_id=pod_id, severity="info"
        )

        for file_rec in files:
            file_id = file_rec.get("file_id") or file_rec.get("id")
            file_path = file_rec.get("stored_path") or file_rec.get("file_path", "")
            original_name = file_rec.get("original_name", "unknown")
            mime_type = file_rec.get("mime_type", "application/octet-stream")

            try:
                # 1. Extract metadata
                self._call_function("extract_metadata", file_path=file_path)
                meta = extract_metadata(file_path) if file_path else {}

                # 2. OCR for images and PDFs
                ocr_result = {"text": "", "confidence": 0.0}
                if mime_type.startswith("image/") or mime_type == "application/pdf":
                    self._call_function("run_ocr", file_path=file_path)
                    ocr_result = run_ocr(file_path)

                # 3. Entity extraction from OCR text
                entities = {}
                if ocr_result.get("text"):
                    self._call_function("extract_entities", text_length=len(ocr_result["text"]))
                    entities = extract_entities(ocr_result["text"])

                # 4. AI classification
                classification = self._classify_evidence(original_name, mime_type, ocr_result.get("text",""))

                # 5. Build structured evidence record
                structured = {
                    "file_id": file_id,
                    "original_name": original_name,
                    "evidence_type": file_rec.get("evidence_type", "other"),
                    "ai_classification": classification,
                    "ai_summary": self._generate_summary(original_name, ocr_result.get("text",""), entities),
                    "extracted_text": ocr_result.get("text", "")[:5000],  # truncate
                    "ocr_confidence": ocr_result.get("confidence", 0.0),
                    "entities": entities,
                    "file_metadata": meta,
                    "priority_score": self._calculate_priority(classification, entities),
                    "processing_status": "complete",
                }
                processed.append(structured)

                send_notification(
                    "file_processed", f"File Processed: {original_name}",
                    f"OCR: {ocr_result.get('confidence',0):.0f}% | Entities found: {len(entities.get('persons',[]))} persons",
                    pod_id=pod_id, severity="success"
                )

            except Exception as e:
                errors.append({"file_id": file_id, "error": str(e)})
                logger.error(f"Failed to process file {file_id}: {e}")

        send_notification(
            "agent_complete", "Evidence Intake Complete",
            f"Processed {len(processed)}/{len(files)} files successfully",
            pod_id=pod_id, severity="success" if not errors else "warning"
        )

        return AgentResult(
            agent_name=self.name,
            pod_id=pod_id,
            success=len(processed) > 0 or len(files) == 0,
            output={"processed": processed, "errors": errors, "total": len(files)},
            reasoning=(
                f"Processed {len(processed)} of {len(files)} evidence files. "
                f"OCR applied to image/PDF files. "
                f"Entities extracted and classified."
            ),
        )

    def _classify_evidence(self, name: str, mime: str, text: str) -> str:
        name_l = name.lower()
        text_l = (text or "").lower()[:500]
        if "autopsy" in name_l or "post mortem" in text_l or "cause of death" in text_l:
            return "autopsy_report"
        if "witness" in name_l or "statement" in name_l:
            return "witness_statement"
        if "cdr" in name_l or "call detail" in text_l:
            return "call_detail_record"
        if "gps" in name_l or ".gpx" in name_l:
            return "gps_log"
        if "cctv" in name_l or "surveillance" in name_l:
            return "cctv_footage"
        if mime.startswith("image/"):
            return "photograph"
        if mime.startswith("video/"):
            return "video_evidence"
        if mime == "application/pdf":
            return "document_pdf"
        return "general_evidence"

    def _generate_summary(self, name: str, text: str, entities: dict) -> str:
        person_count = len(entities.get("persons", []))
        location_count = len(entities.get("locations", []))
        snippet = text[:200].replace("\n", " ") if text else ""
        return (
            f"File: {name}. "
            f"Entities: {person_count} persons, {location_count} locations. "
            f"Preview: {snippet}..."
        )

    def _calculate_priority(self, classification: str, entities: dict) -> float:
        base_priority = {
            "autopsy_report": 90, "witness_statement": 75, "call_detail_record": 70,
            "cctv_footage": 85, "gps_log": 65, "photograph": 60, "video_evidence": 80,
            "document_pdf": 50, "general_evidence": 40,
        }.get(classification, 40)
        # Boost for entity-rich files
        boost = min(10, len(entities.get("persons", [])) * 2 + len(entities.get("locations", [])))
        return min(100.0, float(base_priority + boost))
