"""
OCR Service for extracting text from CJIB traffic fine documents.

Supports Tesseract (local) and Google Cloud Vision API.
Extracts structured fields from Dutch CJIB (Centraal Justitieel Incassobureau) fines.
"""

import json
import logging
import re
from pathlib import Path
from typing import Optional

from anthropic import Anthropic
from PIL import Image

from app.config import settings
from app.schemas.schemas import FineExtracted

logger = logging.getLogger(__name__)


def extract_text_tesseract(file_path: str) -> tuple[str, float]:
    """Extract text from an image or PDF using Tesseract OCR."""
    import pytesseract

    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        from pdf2image import convert_from_path

        images = convert_from_path(file_path)
        all_text = []
        total_confidence = 0.0

        for img in images:
            data = pytesseract.image_to_data(img, lang="nld", output_type=pytesseract.Output.DICT)
            page_text = " ".join(
                word for word, conf in zip(data["text"], data["conf"])
                if int(conf) > 0 and word.strip()
            )
            all_text.append(page_text)
            valid_confs = [int(c) for c in data["conf"] if int(c) > 0]
            if valid_confs:
                total_confidence += sum(valid_confs) / len(valid_confs)

        raw_text = "\n".join(all_text)
        avg_confidence = total_confidence / len(images) if images else 0.0
    else:
        img = Image.open(file_path)
        data = pytesseract.image_to_data(img, lang="nld", output_type=pytesseract.Output.DICT)
        raw_text = " ".join(
            word for word, conf in zip(data["text"], data["conf"])
            if int(conf) > 0 and word.strip()
        )
        valid_confs = [int(c) for c in data["conf"] if int(c) > 0]
        avg_confidence = sum(valid_confs) / len(valid_confs) if valid_confs else 0.0

    return raw_text, avg_confidence / 100.0


def extract_text_google_vision(file_path: str) -> tuple[str, float]:
    """Extract text using Google Cloud Vision API."""
    from google.cloud import vision

    client = vision.ImageAnnotatorClient()

    path = Path(file_path)
    with open(file_path, "rb") as f:
        content = f.read()

    if path.suffix.lower() == ".pdf":
        # For PDFs, use document_text_detection with PDF input
        image = vision.Image(content=content)
        response = client.document_text_detection(image=image)
    else:
        image = vision.Image(content=content)
        response = client.document_text_detection(image=image)

    if response.error.message:
        raise ValueError(f"Google Vision API error: {response.error.message}")

    raw_text = response.full_text_annotation.text if response.full_text_annotation else ""
    confidence = (
        response.full_text_annotation.pages[0].confidence
        if response.full_text_annotation and response.full_text_annotation.pages
        else 0.0
    )

    return raw_text, confidence


def extract_text(file_path: str) -> tuple[str, float]:
    """Extract text from a file using the configured OCR engine."""
    if settings.ocr_engine == "google_vision":
        return extract_text_google_vision(file_path)
    return extract_text_tesseract(file_path)


def parse_fine_with_llm(raw_text: str) -> FineExtracted:
    """
    Use Claude to extract structured fine data from raw OCR text.
    This handles the messy, imperfect OCR output and extracts clean fields.
    """
    client = Anthropic(api_key=settings.anthropic_api_key)

    extraction_prompt = f"""Je bent een expert in het lezen van Nederlandse CJIB-beschikkingen (verkeersboetes).
Analyseer de volgende OCR-tekst van een CJIB-beschikking en extraheer de volgende velden.
Geef het resultaat als een JSON-object.

Velden om te extraheren:
- beschikkingsnummer: Het unieke nummer van de beschikking (vaak begint met CJIB of is een lang nummer)
- overtreding_datum: Datum van de overtreding (formaat: YYYY-MM-DD)
- feitcode: De feitcode van de overtreding (bijv. R552, VA006, etc.)
- omschrijving: Korte omschrijving van de overtreding
- locatie: Locatie waar de overtreding plaatsvond
- bedrag: Het boetebedrag in euro's (als getal, zonder eurotoken)
- instantie: De handhavende instantie (bijv. Politie Eenheid Amsterdam, Gemeente Rotterdam, etc.)

Als een veld niet gevonden kan worden, gebruik dan null.

OCR Tekst:
{raw_text}

Geef ALLEEN het JSON-object terug, zonder extra tekst of uitleg."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": extraction_prompt}],
    )

    response_text = response.content[0].text.strip()

    # Extract JSON from response (handle markdown code blocks)
    json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
    if not json_match:
        logger.error(f"Could not extract JSON from LLM response: {response_text}")
        return FineExtracted()

    try:
        data = json.loads(json_match.group())
        return FineExtracted(**data)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse LLM extraction response: {e}")
        return FineExtracted()


def process_document(file_path: str) -> tuple[FineExtracted, str, float]:
    """
    Full OCR pipeline: extract text, then parse with LLM.

    Returns:
        Tuple of (extracted_data, raw_text, confidence_score)
    """
    logger.info(f"Starting OCR processing for: {file_path}")

    raw_text, confidence = extract_text(file_path)
    logger.info(f"OCR completed with confidence: {confidence:.2f}")

    if not raw_text.strip():
        logger.warning("OCR produced empty text")
        return FineExtracted(), "", 0.0

    extracted = parse_fine_with_llm(raw_text)
    logger.info(f"LLM extraction complete: {extracted.beschikkingsnummer}")

    return extracted, raw_text, confidence
