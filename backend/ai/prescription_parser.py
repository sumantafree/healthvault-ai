"""
HealthVault AI — Prescription Parser
Extracts structured medicine data from prescription images/PDFs.

Reuses the OCR pipeline from Sprint 2; adds a medicine-specific LLM extraction step.

Output: ParsedPrescription with a list of ExtractedMedicine objects,
each mapping 1:1 to a Medicine DB row.
"""
import json
import logging
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from tenacity import retry, stop_after_attempt, wait_exponential

from ai.ocr import assess_ocr_quality, extract_text
from ai.prompts import (
    PROMPT_VERSION,
    SYSTEM_PRESCRIPTION_PARSER,
    build_prescription_parser_prompt,
)
from config import settings

log = logging.getLogger(__name__)


# ── Output Models ─────────────────────────────────────────────────────────────

class ExtractedMedicine(BaseModel):
    name: str
    generic_name: Optional[str] = None
    dosage: Optional[str] = None
    form: Optional[str] = None
    frequency: Optional[str] = None
    instructions: Optional[str] = None
    duration_days: Optional[int] = None

    @field_validator("form")
    @classmethod
    def validate_form(cls, v: Optional[str]) -> Optional[str]:
        allowed = {"tablet", "capsule", "syrup", "injection", "cream", "drops", "inhaler", "other"}
        if v and v.lower() not in allowed:
            return "other"
        return v.lower() if v else None


class ParsedPrescription(BaseModel):
    doctor_name: Optional[str] = None
    hospital_name: Optional[str] = None
    prescribed_date: Optional[str] = None
    valid_until: Optional[str] = None
    medicines: list[ExtractedMedicine] = Field(default_factory=list)
    prompt_version: str = PROMPT_VERSION

    @property
    def prescribed_date_as_date(self) -> Optional[date]:
        if not self.prescribed_date:
            return None
        try:
            return date.fromisoformat(self.prescribed_date)
        except ValueError:
            return None

    @property
    def valid_until_as_date(self) -> Optional[date]:
        if not self.valid_until:
            return None
        try:
            return date.fromisoformat(self.valid_until)
        except ValueError:
            return None


# ── Main Entry Point ───────────────────────────────────────────────────────────

async def parse_prescription_file(contents: bytes, mime_type: str) -> tuple[str, ParsedPrescription]:
    """
    Full pipeline: OCR → LLM extraction.
    Returns (raw_text, ParsedPrescription).
    """
    # Step 1: OCR
    raw_text = await extract_text(contents, mime_type)
    quality = assess_ocr_quality(raw_text)
    log.info("prescription_parser.ocr_done", quality=quality["quality"], chars=quality["char_count"])

    if len(raw_text.strip()) < 30:
        log.warning("prescription_parser.text_too_short")
        return raw_text, ParsedPrescription(medicines=[])

    # Step 2: LLM extraction
    parsed = await parse_prescription_text(raw_text)
    return raw_text, parsed


async def parse_prescription_text(raw_text: str) -> ParsedPrescription:
    """Parse already-extracted text into structured prescription data."""
    if settings.AI_PROVIDER == "gemini":
        raw_json = await _parse_with_gemini(raw_text)
    else:
        raw_json = await _parse_with_openai(raw_text)

    return _safe_parse(raw_json)


# ── OpenAI ────────────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _parse_with_openai(raw_text: str) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PRESCRIPTION_PARSER},
            {"role": "user",   "content": build_prescription_parser_prompt(raw_text)},
        ],
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=2000,
    )
    log.info("prescription_parser.openai_done", tokens=response.usage.total_tokens)
    return response.choices[0].message.content


# ── Gemini ─────────────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _parse_with_gemini(raw_text: str) -> str:
    import asyncio
    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=SYSTEM_PRESCRIPTION_PARSER,
        generation_config=genai.GenerationConfig(
            temperature=0,
            response_mime_type="application/json",
        ),
    )
    response = await asyncio.to_thread(
        model.generate_content,
        build_prescription_parser_prompt(raw_text),
    )
    log.info("prescription_parser.gemini_done")
    return response.text


# ── JSON Parser ────────────────────────────────────────────────────────────────

def _safe_parse(raw_json: str) -> ParsedPrescription:
    try:
        data = json.loads(raw_json)
        medicines = [
            ExtractedMedicine(**m)
            for m in data.get("medicines", [])
            if isinstance(m, dict) and m.get("name")
        ]
        return ParsedPrescription(
            doctor_name=data.get("doctor_name"),
            hospital_name=data.get("hospital_name"),
            prescribed_date=data.get("prescribed_date"),
            valid_until=data.get("valid_until"),
            medicines=medicines,
        )
    except (json.JSONDecodeError, Exception) as exc:
        log.error("prescription_parser.parse_error", error=str(exc), raw=raw_json[:300])
        return ParsedPrescription(medicines=[])
