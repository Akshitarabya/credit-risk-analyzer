"""
OCR service: pure text-extraction mechanics. Knows nothing about documents,
loan applications, or the database — mirrors ml_service.py's role in
Module 3 (the only module that touches the actual extraction engine).

Two paths depending on file type:
  - PDF: try extracting the embedded text layer directly via pypdf first
    (fast, no OCR needed — common for digitally-generated bank statements).
    If there's no text layer (a scanned PDF with no embedded text), this
    intentionally returns no text rather than rasterizing pages — adding
    pdf2image/poppler just for that case was scoped out (see the Module 5
    plan) to avoid a second system dependency beyond Tesseract.
  - JPEG/PNG: OCR via pytesseract (wraps the Tesseract engine).
"""
import io
import re
from dataclasses import dataclass, field

import pytesseract
from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader
from pypdf.errors import PdfReadError


@dataclass
class OCRResult:
    raw_text: str
    confidence: float | None
    extracted_fields: dict = field(default_factory=dict)


class OCRExtractionError(Exception):
    """
    Raised when the file's content can't actually be processed, even though
    it passed the magic-byte MIME check (e.g. a truncated/corrupt image, or
    a PDF whose structure pypdf can't parse). The caller (document_service)
    catches this and marks the document OCR_FAILED without failing the
    upload itself.
    """
    pass


# Illustrative structured extraction only — a single regex-based heuristic
# to demonstrate pulling a structured field out of OCR text, not a full
# document-understanding pipeline. Looks for a currency-like amount, useful
# as a rough signal on income_proof documents.
_CURRENCY_AMOUNT_PATTERN = re.compile(r"\$?\s?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)")


def _extract_heuristic_fields(raw_text: str) -> dict:
    fields: dict = {}
    amounts = _CURRENCY_AMOUNT_PATTERN.findall(raw_text)
    if amounts:
        # Take the largest matched amount as a rough "detected income/amount"
        # signal — genuinely a heuristic, not a claim of accurate parsing.
        cleaned = [float(a.replace(",", "")) for a in amounts]
        fields["detected_largest_amount"] = max(cleaned)
    return fields


def extract_from_image(content: bytes) -> OCRResult:
    try:
        image = Image.open(io.BytesIO(content))
        image.load()  # forces Pillow to actually decode the image now,
        # surfacing corrupt-file errors here rather than later.
    except UnidentifiedImageError as exc:
        raise OCRExtractionError("The image file is corrupt or unreadable.") from exc

    try:
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    except pytesseract.TesseractError as exc:
        raise OCRExtractionError(f"Tesseract OCR failed: {exc}") from exc

    words = [w for w in ocr_data.get("text", []) if w.strip()]
    raw_text = " ".join(words)

    confidences = [int(c) for c in ocr_data.get("conf", []) if c not in ("-1", -1)]
    avg_confidence = (sum(confidences) / len(confidences) / 100) if confidences else None

    return OCRResult(
        raw_text=raw_text,
        confidence=avg_confidence,
        extracted_fields=_extract_heuristic_fields(raw_text),
    )


def extract_from_pdf(content: bytes) -> OCRResult:
    try:
        reader = PdfReader(io.BytesIO(content))
    except PdfReadError as exc:
        raise OCRExtractionError("The PDF file is corrupt or unreadable.") from exc

    if len(reader.pages) == 0:
        raise OCRExtractionError("The PDF has no pages.")

    try:
        raw_text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception as exc:  # pypdf can raise a variety of parser errors on malformed PDFs
        raise OCRExtractionError(f"Could not extract text from this PDF: {exc}") from exc

    if not raw_text:
        raise OCRExtractionError(
            "This PDF has no embedded text layer (likely a scanned image PDF). "
            "Scanned-PDF OCR isn't supported — please upload a JPEG/PNG photo instead."
        )

    return OCRResult(
        raw_text=raw_text,
        confidence=None,  # pypdf's text layer has no meaningful "confidence" concept
        extracted_fields=_extract_heuristic_fields(raw_text),
    )


def extract_text(content: bytes, mime_type: str) -> OCRResult:
    if mime_type == "application/pdf":
        return extract_from_pdf(content)
    if mime_type in ("image/jpeg", "image/png"):
        return extract_from_image(content)
    raise OCRExtractionError(f"No OCR handler for MIME type '{mime_type}'.")