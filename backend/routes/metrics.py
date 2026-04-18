"""
HealthVault AI — Health Metrics Routes
Store and query individual health data points + trend analysis.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import CurrentUser
from models.family_member import FamilyMember
from models.health_metric import HealthMetric
from schemas.health_metric import (
    HealthMetricCreate,
    HealthMetricResponse,
    MetricTrend,
    MetricTrendPoint,
)

router = APIRouter(prefix="/metrics", tags=["Health Metrics"])


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _verify_family_member(
    family_member_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> FamilyMember:
    result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.id == family_member_id,
            FamilyMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found.")
    return member


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/", response_model=HealthMetricResponse, status_code=201, summary="Add a health metric")
async def create_metric(
    payload: HealthMetricCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> HealthMetric:
    await _verify_family_member(payload.family_member_id, current_user.id, db)

    metric = HealthMetric(**payload.model_dump())
    db.add(metric)
    await db.commit()
    await db.refresh(metric)
    return metric


@router.get("/", response_model=List[HealthMetricResponse], summary="List metrics for a member")
async def list_metrics(
    family_member_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    category: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(100, le=500),
) -> List[HealthMetric]:
    await _verify_family_member(family_member_id, current_user.id, db)

    query = (
        select(HealthMetric)
        .where(HealthMetric.family_member_id == family_member_id)
        .order_by(HealthMetric.measured_at.desc())
        .limit(limit)
    )
    if category:
        query = query.where(HealthMetric.category == category)
    if status_filter:
        query = query.where(HealthMetric.status == status_filter)

    result = await db.execute(query)
    return result.scalars().all()


@router.get(
    "/trends",
    response_model=MetricTrend,
    summary="Get trend data for a specific test across time",
)
async def get_metric_trend(
    family_member_id: uuid.UUID,
    test_name: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
) -> MetricTrend:
    await _verify_family_member(family_member_id, current_user.id, db)

    query = (
        select(HealthMetric)
        .where(
            HealthMetric.family_member_id == family_member_id,
            HealthMetric.test_name == test_name,
        )
        .order_by(HealthMetric.measured_at.asc())
    )
    if from_date:
        query = query.where(HealthMetric.measured_at >= from_date)
    if to_date:
        query = query.where(HealthMetric.measured_at <= to_date)

    result = await db.execute(query)
    metrics = result.scalars().all()

    if not metrics:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for test '{test_name}'.",
        )

    latest = metrics[-1]
    return MetricTrend(
        test_name=test_name,
        unit=latest.unit,
        normal_range_min=latest.normal_range_min,
        normal_range_max=latest.normal_range_max,
        data_points=[
            MetricTrendPoint(
                measured_at=m.measured_at,
                value=float(m.value),
                status=m.status,
            )
            for m in metrics
        ],
    )


@router.get(
    "/abnormal",
    response_model=List[HealthMetricResponse],
    summary="Get all abnormal metrics for a family member",
)
async def list_abnormal_metrics(
    family_member_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> List[HealthMetric]:
    await _verify_family_member(family_member_id, current_user.id, db)

    result = await db.execute(
        select(HealthMetric)
        .where(
            HealthMetric.family_member_id == family_member_id,
            HealthMetric.status.in_(["abnormal_low", "abnormal_high"]),
        )
        .order_by(HealthMetric.measured_at.desc())
    )
    return result.scalars().all()


@router.delete("/{metric_id}", status_code=204, summary="Delete a metric")
async def delete_metric(
    metric_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(HealthMetric)
        .join(FamilyMember, FamilyMember.id == HealthMetric.family_member_id)
        .where(
            HealthMetric.id == metric_id,
            FamilyMember.user_id == current_user.id,
        )
    )
    metric = result.scalar_one_or_none()
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found.")
    await db.delete(metric)
    await db.commit()
