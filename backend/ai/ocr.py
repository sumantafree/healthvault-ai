"""
HealthVault AI — OCR Pipeline
Extracts text from uploaded health documents (PDF and images).

Strategy:
  1. PDF with selectable text → PyPDF2 direct extraction (fast)
  2. PDF without text (scanned) → PyMuPDF renders pages → Tesseract OCR
  3. Image files → Tesseract OCR directly
  4. Fallback: LLM cleanup of noisy OCR via prompts.build_ocr_cleanup_prompt
"""
import asyncio
import io
import logging
from typing import Optional

import pytesseract
from PIL import Image

from config import settings

log = logging.getLogger(__name__)

# Configure Tesseract binary path
pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

# Tesseract config: OEM 3 (LSTM + Legacy), PSM 3 (auto page seg)
_TESS_CONFIG = "--oem 3 --psm 3"
_MIN_TEXT_LENGTH = 100  # chars below which we consider PDF text extraction failed


# ── Public API ────────────────────────────────────────────────────────────────

async def extract_text(contents: bytes, mime_type: str) -> str:
    """
    Main entry point. Dispatches to the correct extraction method.
    Returns extracted text or raises ValueError if extraction fails.
    """
    if mime_type == "application/pdf":
        return await _extract_from_pdf(contents)
    elif mime_type.startswith("image/"):
        return await asyncio.to_thread(_extract_from_image_bytes, contents)
    else:
        raise ValueError(f"Unsupported MIME type for OCR: {mime_type}")


# ── PDF Extraction ─────────────────────────────────────────────────────────────

async def _extract_from_pdf(contents: bytes) -> str:
    """
    Two-pass strategy:
      Pass 1 — PyPDF2 direct text extraction (for text-based PDFs)
      Pass 2 — PyMuPDF render → Tesseract (for scanned PDFs)
    """
    # Pass 1: try direct text extraction
    direct_text = await asyncio.to_thread(_pypdf2_extract, contents)

    if len(direct_text.strip()) >= _MIN_TEXT_LENGTH:
        log.info("ocr.pdf_direct_extract", chars=len(direct_text))
        return direct_text

    # Pass 2: render pages to images and OCR
    log.info("ocr.pdf_fallback_to_image_ocr", direct_chars=len(direct_text))
    image_text = await asyncio.to_thread(_pymupdf_render_and_ocr, contents)

    combined = (direct_text + "\n" + image_text).strip()
    if not combined:
        raise ValueError("Could not extract any text from the PDF.")

    return combined


def _pypdf2_extract(contents: bytes) -> str:
    """Extract selectable text from a PDF using PyPDF2."""
    try:
        import PyPDF2

        reader = PyPDF2.PdfReader(io.BytesIO(contents))
        pages_text = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages_text.append(text)
        return "\n".join(pages_text)
    except Exception as exc:
        log.warning("ocr.pypdf2_error", error=str(exc))
        return ""


def _pymupdf_render_and_ocr(contents: bytes, max_pages: int = 10) -> str:
    """
    Render each PDF page to a high-DPI image using PyMuPDF (fitz),
    then run Tesseract OCR on each page image.
    """
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=contents, filetype="pdf")
        pages_text = []
        page_count = min(len(doc), max_pages)

        for page_num in range(page_count):
            page = doc[page_num]
            # 200 DPI matrix for good OCR accuracy
            mat = fitz.Matrix(200 / 72, 200 / 72)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_bytes = pix.tobytes("png")
            page_img = Image.open(io.BytesIO(img_bytes))
            page_text = pytesseract.image_to_string(page_img, config=_TESS_CONFIG)
            pages_text.append(page_text)
            log.info("ocr.page_done", page=page_num + 1, chars=len(page_text))

        if len(doc) > max_pages:
            log.warning("ocr.truncated_pdf", total=len(doc), processed=max_pages)

        return "\n".join(pages_text)

    except ImportError:
        log.warning("ocr.pymupdf_not_installed — falling back to pillow/pdf2image")
        return _pdf2image_fallback(contents, max_pages)
    except Exception as exc:
        log.error("ocr.pymupdf_error", error=str(exc))
        return ""


def _pdf2image_fallback(contents: bytes, max_pages: int = 10) -> str:
    """
    Fallback: use pdf2image (requires poppler) if PyMuPDF isn't available.
    """
    try:
        from pdf2image import convert_from_bytes

        images = convert_from_bytes(contents, dpi=200, last_page=max_pages)
        return "\n".join(
            pytesseract.image_to_string(img, config=_TESS_CONFIG)
            for img in images
        )
    except Exception as exc:
        log.error("ocr.pdf2image_error", error=str(exc))
        return ""


# ── Image Extraction ──────────────────────────────────────────────────────────

def _extract_from_image_bytes(contents: bytes) -> str:
    """Run Tesseract on a raw image (JPEG, PNG, TIFF, WEBP)."""
    try:
        img = Image.open(io.BytesIO(contents))
        img = _preprocess_image(img)
        text = pytesseract.image_to_string(img, config=_TESS_CONFIG)
        log.info("ocr.image_extract", chars=len(text))
        return text
    except Exception as exc:
        log.error("ocr.image_error", error=str(exc))
        raise ValueError(f"OCR failed on image: {str(exc)}")


def _preprocess_image(img: Image.Image) -> Image.Image:
    """
    Improve OCR accuracy with basic pre-processing:
      - Convert to grayscale
      - Resize to at least 300 DPI equivalent if small
    """
    img = img.convert("L")  # grayscale

    # Scale up small images for better OCR
    w, h = img.size
    if max(w, h) < 1500:
        scale = 1500 / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    return img


# ── Quality Assessment ─────────────────────────────────────────────────────────

def assess_ocr_quality(text: str) -> dict:
    """
    Returns a simple quality score for the extracted text.
    Used to decide whether to attempt LLM cleanup.
    """
    words = text.split()
    digit_ratio = sum(c.isdigit() for c in text) / max(len(text), 1)
    alpha_ratio = sum(c.isalpha() for c in text) / max(len(text), 1)
    has_numbers = digit_ratio > 0.02
    has_words = alpha_ratio > 0.3

    quality = "good"
    if len(words) < 20 or not has_numbers:
        quality = "poor"
    elif alpha_ratio < 0.4:
        quality = "fair"

    return {
        "quality": quality,
        "word_count": len(words),
        "char_count": len(text),
        "digit_ratio": round(digit_ratio, 3),
        "alpha_ratio": round(alpha_ratio, 3),
    }
