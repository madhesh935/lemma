"""
Lemma Function: OCR
===================
Extracts text from image or PDF files using Tesseract (local) or cloud OCR.
Independently callable with typed input/output.
"""
from __future__ import annotations
import logging
from typing import Optional
from pathlib import Path

from config import OCR_ENGINE

logger = logging.getLogger("aegis.fn.ocr")


def run_ocr(
    file_path: str,
    language: str = "eng",
    dpi: int = 300,
) -> dict:
    """
    Extract text from an image or PDF file.

    Args:
        file_path: Absolute path to the file.
        language:  Tesseract language code (default: eng).
        dpi:       Resolution for PDF rendering.

    Returns:
        {
          "text": str,
          "page_count": int,
          "confidence": float,
          "engine": str,
          "error": Optional[str],
        }
    """
    result = {"text": "", "page_count": 1, "confidence": 0.0, "engine": OCR_ENGINE, "error": None}

    try:
        path = Path(file_path)
        if not path.exists():
            result["error"] = f"File not found: {file_path}"
            return result

        suffix = path.suffix.lower()

        if OCR_ENGINE == "tesseract":
            result = _run_tesseract(str(path), language, dpi, result)
        elif OCR_ENGINE == "google_vision":
            result = _run_google_vision(str(path), result)
        else:
            result["text"] = _read_text_fallback(str(path), suffix)
            result["engine"] = "fallback"

    except Exception as e:
        logger.error(f"OCR error for {file_path}: {e}")
        result["error"] = str(e)

    logger.info(f"OCR complete: {len(result['text'])} chars extracted from {file_path}")
    return result


def _run_tesseract(file_path: str, language: str, dpi: int, result: dict) -> dict:
    try:
        import pytesseract
        from PIL import Image

        suffix = Path(file_path).suffix.lower()
        if suffix == ".pdf":
            result = _ocr_pdf_tesseract(file_path, language, dpi, result)
        else:
            img = Image.open(file_path)
            data = pytesseract.image_to_data(img, lang=language, output_type=pytesseract.Output.DICT)
            words = [w for w, c in zip(data["text"], data["conf"]) if w.strip() and int(c) > 0]
            confidences = [int(c) for c in data["conf"] if int(c) > 0]
            result["text"] = " ".join(words)
            result["confidence"] = sum(confidences) / len(confidences) if confidences else 0.0
    except ImportError:
        logger.warning("pytesseract not installed, using text fallback.")
        result["text"] = _read_text_fallback(file_path, Path(file_path).suffix.lower())
        result["engine"] = "fallback"
    return result


def _ocr_pdf_tesseract(file_path: str, language: str, dpi: int, result: dict) -> dict:
    try:
        from pdf2image import convert_from_path
        import pytesseract

        pages = convert_from_path(file_path, dpi=dpi)
        all_text = []
        for page in pages:
            text = pytesseract.image_to_string(page, lang=language)
            all_text.append(text)
        result["text"] = "\n\n--- PAGE BREAK ---\n\n".join(all_text)
        result["page_count"] = len(pages)
        result["confidence"] = 75.0  # approximate for PDFs
    except ImportError:
        result["text"] = _read_text_fallback(file_path, ".pdf")
        result["engine"] = "fallback"
    return result


def _run_google_vision(file_path: str, result: dict) -> dict:
    """Google Cloud Vision OCR (requires GOOGLE_VISION_API_KEY)."""
    try:
        from google.cloud import vision
        client = vision.ImageAnnotatorClient()
        with open(file_path, "rb") as f:
            content = f.read()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        texts = response.text_annotations
        if texts:
            result["text"] = texts[0].description
            result["confidence"] = 95.0
    except Exception as e:
        logger.warning(f"Google Vision failed: {e}. Using fallback.")
        result["text"] = _read_text_fallback(file_path, Path(file_path).suffix.lower())
        result["engine"] = "fallback"
    return result


def _read_text_fallback(file_path: str, suffix: str) -> str:
    """Plain text fallback for .txt and .json files."""
    if suffix in (".txt", ".json", ".csv"):
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception:
            pass
    return f"[Binary file: {Path(file_path).name} — OCR not available]"
