from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from database import get_db
from models.developer import Developer
from models.user import User
from models.task import Task, TaskStatus
from routers.auth import get_current_user, require_boss
from services.assignment_engine import assignment_engine

router = APIRouter()


@router.get("/")
async def list_team(
    project_id: Optional[int] = Query(None),
    db: AsyncSession           = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    """Boss: full team overview with workload stats."""
    q = select(Developer)
    if project_id:
        q = q.where(Developer.project_id == project_id)
    result = await db.execute(q)
    developers = result.scalars().all()

    dev_dicts = [
        {
            "id":           d.id,
            "name":         d.user.full_name if d.user else f"Dev {d.id}",
            "role":         d.role,
            "skills":       d.skills,
            "is_available": d.is_available,
            "open_tasks":   d.open_tasks,
            "velocity":     d.velocity,
            "github_username": d.github_username,
        }
        for d in developers
    ]

    return {
        "team":     dev_dicts,
        "workload": assignment_engine.workload_summary(dev_dicts),
    }


@router.get("/{developer_id}")
async def get_developer(
    developer_id: int,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dev = await _get_or_404(db, developer_id)

    # Fetch their open tasks
    tasks_result = await db.execute(
        select(Task).where(
            Task.assigned_to == developer_id,
            Task.status.notin_([TaskStatus.DONE]),
        )
    )
    open_tasks = tasks_result.scalars().all()

    return {
        "developer": dev,
        "open_tasks": [
            {"id": t.id, "title": t.title, "status": t.status, "priority": t.priority}
            for t in open_tasks
        ],
    }


@router.patch("/{developer_id}/availability")
async def toggle_availability(
    developer_id: int,
    is_available: bool,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(require_boss),
):
    dev = await _get_or_404(db, developer_id)
    dev.is_available = is_available
    await db.flush()
    return {"developer_id": developer_id, "is_available": is_available}


@router.get("/workload/summary")
async def get_workload_summary(
    project_id: Optional[int] = Query(None),
    db: AsyncSession           = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    """AI assignment engine workload view."""
    q = select(Developer)
    if project_id:
        q = q.where(Developer.project_id == project_id)
    result = await db.execute(q)
    devs = result.scalars().all()

    dev_dicts = [
        {"id": d.id, "name": f"Dev {d.id}", "role": d.role,
         "open_tasks": d.open_tasks, "velocity": d.velocity}
        for d in devs
    ]
    return assignment_engine.workload_summary(dev_dicts)


# ─── Helper ──────────────────────────────────────────────────────────────────
async def _get_or_404(db: AsyncSession, developer_id: int) -> Developer:
    result = await db.execute(select(Developer).where(Developer.id == developer_id))
    dev    = result.scalar_one_or_none()
    if not dev:
        raise HTTPException(status_code=404, detail="Developer not found")
    return dev
