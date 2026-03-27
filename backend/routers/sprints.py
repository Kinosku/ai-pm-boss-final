from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from database import get_db
from models.sprint import Sprint, SprintStatus
from models.task import Task, TaskStatus
from models.user import User
from schemas.sprint import SprintCreate, SprintUpdate, SprintResponse, SprintSummary, SprintStats
from routers.auth import get_current_user, require_boss

router = APIRouter()


@router.get("/", response_model=List[SprintResponse])
async def list_sprints(
    project_id: Optional[int]       = Query(None),
    status:     Optional[SprintStatus] = Query(None),
    db: AsyncSession                 = Depends(get_db),
    current_user: User               = Depends(get_current_user),
):
    q = select(Sprint)
    if project_id: q = q.where(Sprint.project_id == project_id)
    if status:     q = q.where(Sprint.status     == status)
    result = await db.execute(q.order_by(Sprint.start_date.desc()))
    return result.scalars().all()


@router.post("/", response_model=SprintResponse, status_code=status.HTTP_201_CREATED)
async def create_sprint(
    payload: SprintCreate,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(require_boss),
):
    sprint = Sprint(**payload.model_dump())
    db.add(sprint)
    await db.flush()
    await db.refresh(sprint)
    return sprint


@router.get("/active", response_model=List[SprintSummary])
async def get_active_sprints(
    project_id: Optional[int] = Query(None),
    db: AsyncSession           = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    q = select(Sprint).where(Sprint.status == SprintStatus.ACTIVE)
    if project_id:
        q = q.where(Sprint.project_id == project_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{sprint_id}", response_model=SprintResponse)
async def get_sprint(
    sprint_id: int,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _get_or_404(db, sprint_id)


@router.patch("/{sprint_id}", response_model=SprintResponse)
async def update_sprint(
    sprint_id: int,
    payload: SprintUpdate,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(require_boss),
):
    sprint = await _get_or_404(db, sprint_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(sprint, field, value)
    await db.flush()
    await db.refresh(sprint)
    return sprint


@router.get("/{sprint_id}/stats", response_model=SprintStats)
async def get_sprint_stats(
    sprint_id: int,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sprint = await _get_or_404(db, sprint_id)

    # Task counts by status
    result = await db.execute(
        select(Task.status, func.count(Task.id))
        .where(Task.sprint_id == sprint_id)
        .group_by(Task.status)
    )
    task_counts = {row[0]: row[1] for row in result.all()}

    return SprintStats(
        sprint_id        = sprint.id,
        sprint_name      = sprint.name,
        points_planned   = sprint.points_planned,
        points_completed = sprint.points_completed,
        velocity         = sprint.velocity,
        health_score     = sprint.health_score,
        task_counts      = task_counts,
    )


@router.post("/{sprint_id}/start", response_model=SprintResponse)
async def start_sprint(
    sprint_id: int,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(require_boss),
):
    from datetime import datetime
    sprint = await _get_or_404(db, sprint_id)
    sprint.status     = SprintStatus.ACTIVE
    sprint.start_date = sprint.start_date or datetime.utcnow()
    await db.flush()
    await db.refresh(sprint)
    return sprint


@router.post("/{sprint_id}/complete", response_model=SprintResponse)
async def complete_sprint(
    sprint_id: int,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(require_boss),
):
    from datetime import datetime
    sprint = await _get_or_404(db, sprint_id)
    sprint.status   = SprintStatus.COMPLETED
    sprint.end_date = sprint.end_date or datetime.utcnow()
    await db.flush()
    await db.refresh(sprint)
    return sprint


# ─── Helper ──────────────────────────────────────────────────────────────────
async def _get_or_404(db: AsyncSession, sprint_id: int) -> Sprint:
    result = await db.execute(select(Sprint).where(Sprint.id == sprint_id))
    sprint = result.scalar_one_or_none()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    return sprint
