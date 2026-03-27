from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from database import get_db
from models.risk_alert import RiskAlert, RiskSeverity, RiskStatus
from models.user import User
from schemas.risk_alert import (
    RiskAlertCreate, RiskAlertUpdate,
    RiskAlertResponse, RiskAlertSummary,
    RiskAnalyzeRequest, RiskCounts,
)
from routers.auth import get_current_user, require_boss
from services.risk_engine import risk_engine

router = APIRouter()


@router.get("/", response_model=List[RiskAlertResponse])
async def list_risk_alerts(
    project_id: Optional[int]         = Query(None),
    sprint_id:  Optional[int]         = Query(None),
    severity:   Optional[RiskSeverity]= Query(None),
    status:     Optional[RiskStatus]  = Query(None),
    db: AsyncSession                   = Depends(get_db),
    current_user: User                 = Depends(get_current_user),
):
    q = select(RiskAlert)
    if project_id: q = q.where(RiskAlert.project_id == project_id)
    if sprint_id:  q = q.where(RiskAlert.sprint_id  == sprint_id)
    if severity:   q = q.where(RiskAlert.severity   == severity)
    if status:     q = q.where(RiskAlert.status      == status)
    result = await db.execute(q.order_by(RiskAlert.created_at.desc()))
    return result.scalars().all()


@router.post("/analyze", response_model=List[RiskAlertResponse])
async def analyze_and_create_risks(
    payload: RiskAnalyzeRequest,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(require_boss),
):
    """Trigger AI risk analysis and persist detected risks."""
    analysis = await risk_engine.analyze(payload.project_id, payload.model_dump())

    created = []
    for risk in analysis.get("risks", []):
        alert = RiskAlert(
            project_id          = payload.project_id,
            sprint_id           = payload.sprint_id,
            alert_id            = risk.get("id"),
            title               = risk.get("title", "Unknown Risk"),
            description         = risk.get("description"),
            recommendation      = risk.get("recommendation"),
            severity            = risk.get("severity", "medium"),
            category            = risk.get("category", "other"),
            affected_developers = risk.get("affected_developers", []),
            affected_tasks      = risk.get("affected_tasks", []),
            detected_by         = risk.get("detected_by", "Delay Prediction Agent"),
            health_score        = analysis.get("sprint_health_score"),
        )
        db.add(alert)
        created.append(alert)

    await db.flush()
    for a in created:
        await db.refresh(a)
    return created


@router.get("/counts", response_model=RiskCounts)
async def get_risk_counts(
    project_id: Optional[int] = Query(None),
    db: AsyncSession           = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    """Dashboard stat cards: High / Medium / Low counts."""
    q = select(RiskAlert.severity, func.count(RiskAlert.id)).where(
        RiskAlert.status == RiskStatus.OPEN
    )
    if project_id:
        q = q.where(RiskAlert.project_id == project_id)
    q = q.group_by(RiskAlert.severity)

    result = await db.execute(q)
    counts = {row[0]: row[1] for row in result.all()}
    total  = sum(counts.values())

    return RiskCounts(
        critical = counts.get(RiskSeverity.CRITICAL, 0),
        high     = counts.get(RiskSeverity.HIGH, 0),
        medium   = counts.get(RiskSeverity.MEDIUM, 0),
        low      = counts.get(RiskSeverity.LOW, 0),
        total    = total,
    )


@router.get("/{alert_id}", response_model=RiskAlertResponse)
async def get_risk_alert(
    alert_id: int,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _get_or_404(db, alert_id)


@router.patch("/{alert_id}", response_model=RiskAlertResponse)
async def update_risk_alert(
    alert_id: int,
    payload: RiskAlertUpdate,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(require_boss),
):
    alert = await _get_or_404(db, alert_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(alert, field, value)
    await db.flush()
    await db.refresh(alert)
    return alert


@router.post("/{alert_id}/resolve", response_model=RiskAlertResponse)
async def resolve_risk_alert(
    alert_id: int,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(require_boss),
):
    from datetime import datetime
    alert = await _get_or_404(db, alert_id)
    alert.status      = RiskStatus.RESOLVED
    alert.resolved_at = datetime.utcnow()
    await db.flush()
    await db.refresh(alert)
    return alert


# ─── Helper ──────────────────────────────────────────────────────────────────
async def _get_or_404(db: AsyncSession, alert_id: int) -> RiskAlert:
    result = await db.execute(select(RiskAlert).where(RiskAlert.id == alert_id))
    alert  = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Risk alert not found")
    return alert
