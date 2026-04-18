"""
HealthVault AI — LLM Report Parser
Converts raw OCR text into structured health metrics using OpenAI or Gemini.

Output contract:
  ParsedReport.metrics → list of ExtractedMetric
  Each metric maps 1:1 to a HealthMetric DB row.
"""
import json
import logging
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from tenacity import retry, stop_after_attempt, wait_exponential

from ai.prompts import (
    PROMPT_VERSION,
    SYSTEM_REPORT_PARSER,
    build_ocr_cleanup_prompt,
    build_parser_prompt,
)
from config import settings

log = logging.getLogger(__name__)


# ── Output Models ─────────────────────────────────────────────────────────────

class ExtractedMetric(BaseModel):
    test_name: str
    value: float
    unit: Optional[str] = None
    normal_range_min: Optional[float] = None
    normal_range_max: Optional[float] = None
    normal_range_text: Optional[str] = None
    status: str = "normal"
    category: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"normal", "borderline", "abnormal_low", "abnormal_high"}
        return v if v in allowed else "normal"


class ParsedReport(BaseModel):
    report_date: Optional[str] = None         # "YYYY-MM-DD" string or None
    lab_name: Optional[str] = None
    doctor_name: Optional[str] = None
    report_type: str = "other"
    metrics: list[ExtractedMetric] = Field(default_factory=list)
    prompt_version: str = PROMPT_VERSION

    @property
    def report_date_as_date(self) -> Optional[date]:
        if not self.report_date:
            return None
        try:
            return date.fromisoformat(self.report_date)
        except ValueError:
            return None

    @property
    def abnormal_metrics(self) -> list[ExtractedMetric]:
        return [m for m in self.metrics if m.status in ("abnormal_low", "abnormal_high")]


# ── Parser ─────────────────────────────────────────────────────────────────────

async def parse_report(raw_text: str, report_type: str = "other") -> ParsedReport:
    """
    Main entry point. Routes to OpenAI or Gemini based on config.
    Retries up to 3 times on transient failures.
    """
    if len(raw_text.strip()) < 50:
        log.warning("parser.text_too_short", chars=len(raw_text))
        return ParsedReport(metrics=[])

    if settings.AI_PROVIDER == "gemini":
        raw_json = await _parse_with_gemini(raw_text, report_type)
    else:
        raw_json = await _parse_with_openai(raw_text, report_type)

    return _safe_parse(raw_json)


async def clean_ocr_text(raw_text: str) -> str:
    """
    Optional LLM cleanup pass for noisy OCR output.
    Only called when OCR quality assessment returns 'fair' or 'poor'.
    """
    if settings.AI_PROVIDER == "gemini":
        return await _gemini_completion(
            system="You clean OCR text. Return only the cleaned text.",
            user=build_ocr_cleanup_prompt(raw_text),
        )
    return await _openai_completion(
        system="You clean OCR text. Return only the cleaned text.",
        user=build_ocr_cleanup_prompt(raw_text),
        json_mode=False,
    )


# ── OpenAI ────────────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _parse_with_openai(raw_text: str, report_type: str) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    prompt = build_parser_prompt(raw_text, report_type)

    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_REPORT_PARSER},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0,           # deterministic extraction
        max_tokens=3000,
    )

    content = response.choices[0].message.content
    log.info(
        "parser.openai_done",
        model=settings.OPENAI_MODEL,
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
    )
    return content


async def _openai_completion(system: str, user: str, json_mode: bool = True) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0,
        max_tokens=2000,
        **kwargs,
    )
    return response.choices[0].message.content


# ── Gemini ─────────────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _parse_with_gemini(raw_text: str, report_type: str) -> str:
    import asyncio

    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=SYSTEM_REPORT_PARSER,
        generation_config=genai.GenerationConfig(
            temperature=0,
            response_mime_type="application/json",
        ),
    )
    prompt = build_parser_prompt(raw_text, report_type)
    response = await asyncio.to_thread(model.generate_content, prompt)
    log.info("parser.gemini_done")
    return response.text


async def _gemini_completion(system: str, user: str) -> str:
    import asyncio

    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=system,
    )
    response = await asyncio.to_thread(model.generate_content, user)
    return response.text


# ── JSON Parser ────────────────────────────────────────────────────────────────

def _safe_parse(raw_json: str) -> ParsedReport:
    """Parse LLM JSON output into ParsedReport. Handles malformed output gracefully."""
    try:
        data = json.loads(raw_json)
        return ParsedReport(**data)
    except (json.JSONDecodeError, Exception) as exc:
        log.error("parser.json_parse_error", error=str(exc), raw=raw_json[:500])
        # Attempt to extract just the metrics array if full parse fails
        try:
            data = json.loads(raw_json)
            metrics_raw = data.get("metrics", [])
            metrics = [ExtractedMetric(**m) for m in metrics_raw if isinstance(m, dict)]
            return ParsedReport(metrics=metrics)
        except Exception:
            return ParsedReport(metrics=[])
