"""
HealthVault AI — AI Pipeline Unit Tests
Tests OCR, parser, and insights modules with mocked LLM calls.
"""
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.insights import (
    GeneratedInsight,
    Recommendation,
    compute_risk_level_from_metrics,
    generate_insights,
)
from ai.ocr import _preprocess_image, assess_ocr_quality
from ai.parser import ExtractedMetric, ParsedReport, _safe_parse
from ai.prompts import PROMPT_VERSION, build_parser_prompt


# ── OCR Tests ─────────────────────────────────────────────────────────────────

class TestOCRQualityAssessment:
    def test_good_quality_text(self):
        text = "Hemoglobin 14.5 g/dL normal range 13.5-17.5 Patient: John Doe Blood test results CBC"
        result = assess_ocr_quality(text)
        assert result["quality"] == "good"
        assert result["word_count"] > 0

    def test_poor_quality_short_text(self):
        result = assess_ocr_quality("abc 1")
        assert result["quality"] == "poor"

    def test_empty_text(self):
        result = assess_ocr_quality("")
        assert result["quality"] == "poor"
        assert result["char_count"] == 0

    def test_digit_ratio_calculated(self):
        text = "1234567890" * 10 + " words here"
        result = assess_ocr_quality(text)
        assert result["digit_ratio"] > 0.5


# ── Parser Tests ──────────────────────────────────────────────────────────────

class TestReportParser:
    def test_safe_parse_valid_json(self):
        raw = json.dumps({
            "report_date": "2024-01-15",
            "lab_name": "City Lab",
            "doctor_name": "Dr. Smith",
            "report_type": "blood_test",
            "metrics": [
                {
                    "test_name": "Hemoglobin",
                    "value": 14.5,
                    "unit": "g/dL",
                    "normal_range_min": 13.5,
                    "normal_range_max": 17.5,
                    "normal_range_text": "13.5-17.5",
                    "status": "normal",
                    "category": "CBC",
                }
            ],
        })
        result = _safe_parse(raw)
        assert isinstance(result, ParsedReport)
        assert len(result.metrics) == 1
        assert result.metrics[0].test_name == "Hemoglobin"
        assert result.metrics[0].value == 14.5
        assert result.lab_name == "City Lab"

    def test_safe_parse_invalid_json(self):
        result = _safe_parse("not json at all {{{")
        assert isinstance(result, ParsedReport)
        assert result.metrics == []

    def test_safe_parse_empty_metrics(self):
        raw = json.dumps({"metrics": [], "report_date": None})
        result = _safe_parse(raw)
        assert result.metrics == []

    def test_metric_status_validation(self):
        metric = ExtractedMetric(
            test_name="Test", value=5.0, status="invalid_status"
        )
        assert metric.status == "normal"  # coerced to normal

    def test_metric_abnormal_detection(self):
        parsed = ParsedReport(
            metrics=[
                ExtractedMetric(test_name="A", value=1.0, status="normal"),
                ExtractedMetric(test_name="B", value=2.0, status="abnormal_high"),
                ExtractedMetric(test_name="C", value=3.0, status="abnormal_low"),
            ]
        )
        assert len(parsed.abnormal_metrics) == 2

    def test_parser_prompt_contains_text(self):
        prompt = build_parser_prompt("Sample OCR text here", "blood_test")
        assert "Sample OCR text" in prompt
        assert "blood_test" in prompt
        assert "JSON" in prompt

    def test_report_date_parsing(self):
        raw = json.dumps({"report_date": "2024-06-15", "metrics": []})
        result = _safe_parse(raw)
        from datetime import date
        assert result.report_date_as_date == date(2024, 6, 15)

    def test_invalid_report_date_returns_none(self):
        raw = json.dumps({"report_date": "not-a-date", "metrics": []})
        result = _safe_parse(raw)
        assert result.report_date_as_date is None

    def test_prompt_version_set(self):
        result = _safe_parse(json.dumps({"metrics": []}))
        assert result.prompt_version == PROMPT_VERSION


# ── Insights Tests ────────────────────────────────────────────────────────────

class TestInsightsEngine:
    def test_risk_level_all_normal(self):
        metrics = [
            {"test_name": "A", "status": "normal"},
            {"test_name": "B", "status": "normal"},
        ]
        assert compute_risk_level_from_metrics(metrics) == "low"

    def test_risk_level_one_abnormal(self):
        metrics = [
            {"test_name": "A", "status": "normal"},
            {"test_name": "B", "status": "abnormal_high"},
        ]
        assert compute_risk_level_from_metrics(metrics) == "moderate"

    def test_risk_level_two_abnormal(self):
        metrics = [{"status": "abnormal_high"} for _ in range(2)]
        assert compute_risk_level_from_metrics(metrics) == "high"

    def test_risk_level_critical(self):
        metrics = [{"status": "abnormal_high"} for _ in range(3)]
        assert compute_risk_level_from_metrics(metrics) == "critical"

    def test_risk_level_borderline(self):
        metrics = [
            {"test_name": "A", "status": "borderline"},
            {"test_name": "B", "status": "borderline"},
        ]
        assert compute_risk_level_from_metrics(metrics) == "moderate"

    @pytest.mark.asyncio
    async def test_generate_insights_empty_metrics(self):
        result = await generate_insights([], {})
        assert isinstance(result, GeneratedInsight)
        assert result.risk_level == "low"
        assert "disclaimer" in result.model_dump()
        assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_generate_insights_mocked_openai(self):
        mock_response = json.dumps({
            "summary": "Blood results show all values within normal range.",
            "risk_level": "low",
            "risk_factors": [],
            "recommendations": [
                {
                    "title": "Consult Your Doctor",
                    "description": "Share this report.",
                    "priority": "high",
                }
            ],
            "disclaimer": "For informational purposes only.",
        })

        with patch("ai.insights._insights_with_openai", new=AsyncMock(return_value=mock_response)):
            from config import settings
            original = settings.AI_PROVIDER
            settings.__dict__["AI_PROVIDER"] = "openai"

            metrics = [{"test_name": "Hemoglobin", "value": 14.5, "status": "normal"}]
            result = await generate_insights(metrics, {"age": 35, "gender": "male"})

            assert result.risk_level == "low"
            assert "normal range" in result.summary
            assert len(result.recommendations) == 1


# ── Integration Smoke Test ────────────────────────────────────────────────────

class TestPipelineIntegration:
    @pytest.mark.asyncio
    async def test_pipeline_skips_on_missing_report(self):
        """Pipeline should not crash on a non-existent report ID."""
        from ai.pipeline import process_report_pipeline

        fake_id = uuid.uuid4()
        # Should complete without raising
        with patch("ai.pipeline.get_db_context") as mock_ctx:
            mock_db = AsyncMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            mock_ctx.return_value.__aenter__.return_value = mock_db
            await process_report_pipeline(fake_id)
