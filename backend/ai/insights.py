"""
HealthVault AI — AI Insights Engine
Generates informational health summaries from structured metric data.

IMPORTANT: This module never produces medical diagnoses.
All output includes a mandatory disclaimer.
"""
import json
import logging
from typing import Optional

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from ai.prompts import (
    PROMPT_VERSION,
    SYSTEM_INSIGHTS,
    build_insights_prompt,
)
from config import settings
from models.ai_insight import DISCLAIMER

log = logging.getLogger(__name__)


# ── Output Model ──────────────────────────────────────────────────────────────

class Recommendation(BaseModel):
    title: str
    description: str
    priority: str = "medium"  # low | medium | high


class GeneratedInsight(BaseModel):
    summary: str
    risk_level: str = "low"
    risk_factors: list[str] = []
    recommendations: list[Recommendation] = []
    disclaimer: str = DISCLAIMER
    model_used: str = ""
    prompt_version: str = PROMPT_VERSION

    def to_db_dict(self) -> dict:
        return {
            "summary": self.summary,
            "risk_level": self.risk_level,
            "risk_factors": self.risk_factors,
            "recommendations": [r.model_dump() for r in self.recommendations],
            "disclaimer": self.disclaimer,
            "model_used": self.model_used,
            "prompt_version": self.prompt_version,
        }


# ── Member Context Builder ─────────────────────────────────────────────────────

def build_member_context(member) -> dict:
    """
    Build a safe, anonymized context object for the LLM.
    Excludes PII (name, DOB) — uses age + gender only.
    """
    return {
        "age": member.age,
        "gender": member.gender,
        "blood_type": member.blood_type if member.blood_type != "unknown" else None,
        "chronic_conditions": member.chronic_conditions or [],
        "allergies": member.allergies or [],
        "bmi": member.bmi,
    }


# ── Main Entry Point ───────────────────────────────────────────────────────────

async def generate_insights(
    metrics: list[dict],
    member_context: dict,
) -> GeneratedInsight:
    """
    Generate health insights from a list of extracted metrics.
    Routes to OpenAI or Gemini based on config.
    """
    if not metrics:
        return GeneratedInsight(
            summary="No health metrics were extracted from this report. Please ensure the document is a valid lab report.",
            risk_level="low",
            risk_factors=[],
            recommendations=[
                Recommendation(
                    title="Upload a Valid Report",
                    description="Please upload a clear scan or PDF of your lab report.",
                    priority="medium",
                )
            ],
        )

    if settings.AI_PROVIDER == "gemini":
        raw_json = await _insights_with_gemini(metrics, member_context)
        model_name = "gemini-1.5-pro"
    else:
        raw_json = await _insights_with_openai(metrics, member_context)
        model_name = settings.OPENAI_MODEL

    insight = _safe_parse_insight(raw_json)
    insight.model_used = model_name
    return insight


# ── OpenAI ────────────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _insights_with_openai(metrics: list[dict], member_context: dict) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    prompt = build_insights_prompt(metrics, member_context, DISCLAIMER)

    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_INSIGHTS},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,        # slight creativity for natural summaries
        max_tokens=1500,
    )

    content = response.choices[0].message.content
    log.info(
        "insights.openai_done",
        tokens=response.usage.total_tokens,
        model=settings.OPENAI_MODEL,
    )
    return content


# ── Gemini ─────────────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _insights_with_gemini(metrics: list[dict], member_context: dict) -> str:
    import asyncio

    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=SYSTEM_INSIGHTS,
        generation_config=genai.GenerationConfig(
            temperature=0.3,
            response_mime_type="application/json",
        ),
    )
    prompt = build_insights_prompt(metrics, member_context, DISCLAIMER)
    response = await asyncio.to_thread(model.generate_content, prompt)
    log.info("insights.gemini_done")
    return response.text


# ── JSON Parser ────────────────────────────────────────────────────────────────

def _safe_parse_insight(raw_json: str) -> GeneratedInsight:
    """Parse LLM JSON into GeneratedInsight. Gracefully degrades on malformed output."""
    try:
        data = json.loads(raw_json)

        # Normalize recommendations list
        recs_raw = data.get("recommendations", [])
        recommendations = []
        for r in recs_raw:
            if isinstance(r, dict):
                recommendations.append(
                    Recommendation(
                        title=r.get("title", ""),
                        description=r.get("description", ""),
                        priority=r.get("priority", "medium"),
                    )
                )

        return GeneratedInsight(
            summary=data.get("summary", "Analysis unavailable."),
            risk_level=_validate_risk_level(data.get("risk_level", "low")),
            risk_factors=data.get("risk_factors", []),
            recommendations=recommendations,
            disclaimer=data.get("disclaimer", DISCLAIMER),
        )
    except (json.JSONDecodeError, Exception) as exc:
        log.error("insights.parse_error", error=str(exc))
        return GeneratedInsight(
            summary="We were unable to generate insights for this report at this time.",
            risk_level="low",
            disclaimer=DISCLAIMER,
        )


def _validate_risk_level(level: str) -> str:
    valid = {"low", "moderate", "high", "critical"}
    return level if level in valid else "low"


# ── Rule-based Risk Scorer (offline fallback) ─────────────────────────────────

def compute_risk_level_from_metrics(metrics: list[dict]) -> str:
    """
    Deterministic risk scoring used when AI is unavailable.
    Based solely on status values — no diagnosis.
    """
    critical_count = sum(1 for m in metrics if m.get("status") in ("abnormal_low", "abnormal_high"))
    borderline_count = sum(1 for m in metrics if m.get("status") == "borderline")

    if critical_count >= 3:
        return "critical"
    if critical_count >= 2:
        return "high"
    if critical_count == 1 or borderline_count >= 2:
        return "moderate"
    return "low"
