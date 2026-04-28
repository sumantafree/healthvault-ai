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
import base64
import io
from typing import Optional

import structlog
from PIL import Image

from config import settings

log = structlog.get_logger(__name__)

_MIN_TEXT_LENGTH = 100  # chars below which we consider PDF text extraction failed

# Optional Tesseract — only used if explicitly available locally. Render's free
# tier doesn't have tesseract installed, so we fall back to Gemini Vision OCR
# for images and rendered PDF pages.
try:
    import pytesseract  # type: ignore
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    # Probe — `get_tesseract_version()` raises if the binary isn't on PATH.
    pytesseract.get_tesseract_version()
    _HAS_TESSERACT = True
except Exception:
    _HAS_TESSERACT = False
    log.info("ocr.tesseract_unavailable_using_gemini_vision")

_TESS_CONFIG = "--oem 3 --psm 3"


# ── Public API ────────────────────────────────────────────────────────────────

async def extract_text(contents: bytes, mime_type: str) -> str:
    """
    Main entry point. Dispatches to the correct extraction method.
    Returns extracted text or raises ValueError if extraction fails.
    """
    if mime_type == "application/pdf":
        return await _extract_from_pdf(contents)
    elif mime_type.startswith("image/"):
        if _HAS_TESSERACT:
            return await asyncio.to_thread(_extract_from_image_bytes, contents)
        return await _extract_from_image_via_gemini(contents, mime_type)
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

    # Pass 2: render pages to images and OCR (Tesseract or Gemini Vision)
    log.info("ocr.pdf_fallback_to_image_ocr", direct_chars=len(direct_text))
    if _HAS_TESSERACT:
        image_text = await asyncio.to_thread(_pymupdf_render_and_ocr, contents)
    else:
        image_text = await _pymupdf_render_and_gemini_ocr(contents)

    combined = (direct_text + "\n" + image_text).strip()
    if not combined:
        raise ValueError("Could not extract any text from the PDF.")

    return combined


async def _pymupdf_render_and_gemini_ocr(contents: bytes, max_pages: int = 5) -> str:
    """Render PDF pages with PyMuPDF, OCR each via Gemini Vision."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        log.error("ocr.pymupdf_not_installed")
        return ""

    def _render_pages() -> list[bytes]:
        doc = fitz.open(stream=contents, filetype="pdf")
        page_count = min(len(doc), max_pages)
        pages = []
        for page_num in range(page_count):
            page = doc[page_num]
            mat = fitz.Matrix(150 / 72, 150 / 72)  # 150 DPI is enough for Gemini
            pix = page.get_pixmap(matrix=mat, alpha=False)
            pages.append(pix.tobytes("png"))
        return pages

    page_images = await asyncio.to_thread(_render_pages)
    log.info("ocr.pdf_rendered_for_gemini", pages=len(page_images))

    texts = []
    for i, img_bytes in enumerate(page_images):
        try:
            page_text = await _extract_from_image_via_gemini(img_bytes, "image/png")
            texts.append(page_text)
            log.info("ocr.gemini_page_done", page=i + 1, chars=len(page_text))
        except Exception as exc:
            log.error("ocr.gemini_page_failed", page=i + 1, error=str(exc))

    return "\n".join(texts)


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
    """Run Tesseract on a raw image. Only used if Tesseract is available."""
    try:
        img = Image.open(io.BytesIO(contents))
        img = _preprocess_image(img)
        text = pytesseract.image_to_string(img, config=_TESS_CONFIG)
        log.info("ocr.image_extract_tesseract", chars=len(text))
        return text
    except Exception as exc:
        log.error("ocr.tesseract_image_error", error=str(exc))
        raise ValueError(f"Tesseract OCR failed on image: {str(exc)}")


async def _extract_from_image_via_gemini(contents: bytes, mime_type: str) -> str:
    """
    Use Gemini Vision to extract text from an image.
    Works for JPEG/PNG/WEBP/HEIC and any image format Gemini supports.
    """
    try:
        import google.generativeai as genai
    except ImportError:
        raise ValueError("google-generativeai not installed; cannot OCR without Tesseract.")

    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured; cannot OCR without Tesseract.")

    genai.configure(api_key=settings.GEMINI_API_KEY)

    # Normalize mime type — Gemini wants e.g. "image/jpeg"
    mime = mime_type or "image/jpeg"
    if not mime.startswith("image/"):
        mime = "image/jpeg"

    prompt = (
        "Extract ALL the text visible in this medical/health document image. "
        "Preserve numbers, units, ranges, and table structure where possible. "
        "Output the raw text exactly as it appears — no summary, no commentary."
    )

    # Try several model names in order. Google has been deprecating older
    # names ("no longer available to new users"); we keep newest-first.
    # Verified available via /debug/gemini-models on this API key.
    candidate_models = [
        "gemini-2.5-flash",
        "gemini-flash-latest",
        "gemini-2.0-flash-001",
        "gemini-2.0-flash-lite-001",
        "gemini-2.5-pro",
        "gemini-pro-latest",
    ]

    def _call(name: str) -> str:
        m = genai.GenerativeModel(name)
        response = m.generate_content(
            [{"mime_type": mime, "data": contents}, prompt],
            generation_config={"temperature": 0.0, "max_output_tokens": 4096},
        )
        return (response.text or "").strip()

    last_err: Optional[Exception] = None
    for name in candidate_models:
        try:
            text = await asyncio.to_thread(_call, name)
            log.info("ocr.image_extract_gemini", model=name, chars=len(text))
            return text
        except Exception as exc:
            log.warning("ocr.gemini_model_failed", model=name, error=str(exc)[:200])
            last_err = exc
            continue

    log.error("ocr.gemini_all_models_failed", error=str(last_err))
    raise ValueError(f"Gemini Vision OCR failed (no model worked): {last_err}")


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
