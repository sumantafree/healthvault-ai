"""
HealthVault AI — AI Processing Pipeline
Orchestrates the full flow: OCR → Clean → Parse → Metrics → Insights → DB update.

Each stage updates report.processing_status so the frontend can show progress.

Stages:
  1. fetch_file       — download file bytes from storage
  2. ocr              — extract raw text
  3. clean            — LLM cleanup if OCR quality is fair/poor
  4. parse            — LLM structured extraction → ExtractedMetric list
  5. save_metrics     — bulk-insert HealthMetric rows
  6. generate_insights — LLM health summary
  7. save_insights    — insert AIInsight row
  8. finalize         — update report status to 'done'
"""
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai.insights import GeneratedInsight, build_member_context, generate_insights
from ai.ocr import assess_ocr_quality, extract_text
from ai.parser import ParsedReport, parse_report
from database import get_db_context
from models.ai_insight import AIInsight
from models.family_member import FamilyMember
from models.health_metric import HealthMetric
from models.health_report import HealthReport

log = structlog.get_logger(__name__)


def _flush(msg: str, **kwargs) -> None:
    """Print to stdout AND structlog so logs appear no matter how logging is
    configured. Render captures stdout reliably; structlog may be buffered."""
    parts = " ".join(f"{k}={v}" for k, v in kwargs.items())
    print(f"[pipeline] {msg} {parts}", flush=True, file=sys.stdout)
    log.info(msg, **kwargs)


# ── Pipeline Entry Point ───────────────────────────────────────────────────────

async def process_report_pipeline(report_id: uuid.UUID) -> None:
    """
    Full AI processing pipeline for a health report.
    Called as a background task after upload.
    All errors are caught — report is marked 'failed' on any unrecoverable error.
    """
    _flush("pipeline.start", report_id=str(report_id))

    async with get_db_context() as db:
        report = await _fetch_report(report_id, db)
        if not report:
            _flush("pipeline.report_not_found", report_id=str(report_id))
            return

        try:
            await _set_status(report, "processing", db)
            _flush("pipeline.status_processing", report_id=str(report_id))

            # Stage 1: Download file
            _flush("pipeline.stage1_download_start", url=report.file_url[:100])
            contents, mime_type = await _download_file(report)
            _flush("pipeline.stage1_download_done", bytes=len(contents), mime=mime_type)

            # Stage 2 + 3: OCR + optional cleanup
            _flush("pipeline.stage2_ocr_start")
            raw_text = await _run_ocr(report, contents, mime_type, db)
            _flush("pipeline.stage2_ocr_done", chars=len(raw_text))

            # Stage 4: LLM parse → structured metrics
            _flush("pipeline.stage4_parse_start")
            parsed = await _run_parser(report, raw_text, db)
            _flush("pipeline.stage4_parse_done", metrics=len(parsed.metrics))

            # Stage 5: Save metrics to DB
            _flush("pipeline.stage5_save_metrics_start")
            metric_dicts = await _save_metrics(report, parsed, db)
            _flush("pipeline.stage5_save_metrics_done")

            # Stage 6 + 7: Generate + save AI insights
            _flush("pipeline.stage6_insights_start")
            member = await _fetch_member(report.family_member_id, db)
            await _run_insights(report, metric_dicts, member, db)
            _flush("pipeline.stage6_insights_done")

            # Stage 8: Finalize
            await _finalize(report, parsed, db)
            _flush("pipeline.complete", report_id=str(report_id),
                   metrics=len(parsed.metrics), risk=report.risk_level)

        except Exception as exc:
            import traceback
            tb = traceback.format_exc()
            _flush("pipeline.failed", report_id=str(report_id), error=str(exc))
            print(tb, flush=True, file=sys.stdout)
            try:
                await _set_status(report, "failed", db, error=f"{type(exc).__name__}: {exc}")
            except Exception as inner:
                _flush("pipeline.failed_to_record_error", inner=str(inner))


# ── Pipeline Stages ────────────────────────────────────────────────────────────

async def _fetch_report(report_id: uuid.UUID, db: AsyncSession) -> Optional[HealthReport]:
    result = await db.execute(select(HealthReport).where(HealthReport.id == report_id))
    return result.scalar_one_or_none()


async def _fetch_member(member_id: uuid.UUID, db: AsyncSession) -> Optional[FamilyMember]:
    result = await db.execute(select(FamilyMember).where(FamilyMember.id == member_id))
    return result.scalar_one_or_none()


async def _set_status(
    report: HealthReport,
    status: str,
    db: AsyncSession,
    error: Optional[str] = None,
) -> None:
    report.processing_status = status
    if error:
        report.processing_error = error[:2000]
    db.add(report)
    await db.commit()


async def _download_file(report: HealthReport) -> tuple[bytes, str]:
    """Download file bytes from Supabase Storage URL."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(report.file_url)
        response.raise_for_status()
    return response.content, report.mime_type or "application/pdf"


async def _run_ocr(
    report: HealthReport,
    contents: bytes,
    mime_type: str,
    db: AsyncSession,
) -> str:
    """Stage 2+3: OCR + optional LLM cleanup."""
    raw_text = await extract_text(contents, mime_type)
    quality = assess_ocr_quality(raw_text)
    log.info("pipeline.ocr_done", quality=quality["quality"], chars=quality["char_count"])

    if quality["quality"] in ("fair", "poor") and len(raw_text) > 20:
        log.info("pipeline.running_ocr_cleanup")
        from ai.parser import clean_ocr_text
        raw_text = await clean_ocr_text(raw_text)

    # Persist raw text for debugging / re-processing
    report.raw_text = raw_text[:50000]  # cap at 50k chars
    db.add(report)
    await db.commit()
    return raw_text


async def _run_parser(
    report: HealthReport,
    raw_text: str,
    db: AsyncSession,
) -> ParsedReport:
    """Stage 4: LLM structured extraction."""
    parsed = await parse_report(raw_text, report.report_type)

    # Update report metadata from parsed data
    if parsed.lab_name and not report.lab_name:
        report.lab_name = parsed.lab_name[:255]
    if parsed.doctor_name and not report.doctor_name:
        report.doctor_name = parsed.doctor_name[:255]
    if parsed.report_date_as_date and not report.report_date:
        report.report_date = parsed.report_date_as_date
    if parsed.report_type and parsed.report_type != "other":
        report.report_type = parsed.report_type

    report.parsed_data = {
        "metrics": [m.model_dump() for m in parsed.metrics],
        "prompt_version": parsed.prompt_version,
        "metric_count": len(parsed.metrics),
        "abnormal_count": len(parsed.abnormal_metrics),
    }
    db.add(report)
    await db.commit()

    log.info("pipeline.parse_done", metrics=len(parsed.metrics))
    return parsed


async def _save_metrics(
    report: HealthReport,
    parsed: ParsedReport,
    db: AsyncSession,
) -> list[dict]:
    """Stage 5: Bulk insert HealthMetric rows."""
    if not parsed.metrics:
        return []

    now = report.report_date or datetime.now(timezone.utc)
    measured_at = datetime.combine(now, datetime.min.time()).replace(tzinfo=timezone.utc) if hasattr(now, 'year') else now

    metric_rows = []
    for m in parsed.metrics:
        metric = HealthMetric(
            family_member_id=report.family_member_id,
            report_id=report.id,
            test_name=m.test_name,
            value=m.value,
            unit=m.unit,
            normal_range_min=m.normal_range_min,
            normal_range_max=m.normal_range_max,
            normal_range_text=m.normal_range_text,
            status=m.status,
            category=m.category,
            measured_at=measured_at,
        )
        db.add(metric)
        metric_rows.append(m.model_dump())

    await db.commit()
    log.info("pipeline.metrics_saved", count=len(metric_rows))
    return metric_rows


async def _run_insights(
    report: HealthReport,
    metric_dicts: list[dict],
    member: Optional[FamilyMember],
    db: AsyncSession,
) -> None:
    """Stage 6+7: Generate and save AI insights."""
    member_context = build_member_context(member) if member else {}
    insight: GeneratedInsight = await generate_insights(metric_dicts, member_context)

    # Persist insight
    ai_insight = AIInsight(
        family_member_id=report.family_member_id,
        report_id=report.id,
        summary=insight.summary,
        risk_level=insight.risk_level,
        risk_factors=insight.risk_factors,
        recommendations={"items": [r.model_dump() for r in insight.recommendations]},
        disclaimer=insight.disclaimer,
        model_used=insight.model_used,
        prompt_version=insight.prompt_version,
    )
    db.add(ai_insight)

    # Propagate risk level up to the report
    report.risk_level = insight.risk_level
    report.ai_summary = insight.summary
    db.add(report)

    await db.commit()
    log.info("pipeline.insights_saved", risk=insight.risk_level)


async def _finalize(report: HealthReport, parsed: ParsedReport, db: AsyncSession) -> None:
    """Stage 8: Mark report as done."""
    report.processing_status = "done"
    db.add(report)
    await db.commit()
