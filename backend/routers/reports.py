from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date, timedelta

from database import get_db
from models.user import User
from models.task import Task, TaskStatus
from models.pull_request import PullRequest, PRStatus
from models.risk_alert import RiskAlert, RiskStatus
from models.sprint import Sprint, SprintStatus
from sqlalchemy import select, func
from schemas.sprint import SprintStats
from routers.auth import get_current_user, require_boss
from services.report_service import report_service, ReportType

router = APIRouter()


@router.post("/generate")
async def generate_report(
    project_id:  int,
    report_type: ReportType   = ReportType.WEEKLY,
    sprint_id:   Optional[int]= Query(None),
    db: AsyncSession           = Depends(get_db),
    current_user: User         = Depends(require_boss),
):
    """Generate an AI report for a project."""
    today = date.today()

    # Gather data
    task_result = await db.execute(
        select(Task.status, func.count(Task.id))
        .where(Task.project_id == project_id)
        .group_by(Task.status)
    )
    task_counts = {row[0]: row[1] for row in task_result.all()}

    pr_result = await db.execute(
        select(PullRequest.status, func.count(PullRequest.id))
        .where(PullRequest.project_id == project_id)
        .group_by(PullRequest.status)
    )
    pr_counts = {row[0]: row[1] for row in pr_result.all()}

    risk_result = await db.execute(
        select(func.count(RiskAlert.id)).where(
            RiskAlert.project_id == project_id,
            RiskAlert.status     == RiskStatus.OPEN,
        )
    )
    active_risks = risk_result.scalar() or 0

    report_data = {
        "project_name":      f"Project {project_id}",
        "period_start":      str(today - timedelta(days=7)),
        "period_end":        str(today),
        "completed_tasks":   task_counts.get(TaskStatus.DONE, 0),
        "total_tasks":       sum(task_counts.values()),
        "points_delivered":  0,
        "points_planned":    0,
        "prs_merged":        pr_counts.get(PRStatus.MERGED, 0),
        "prs_open":          pr_counts.get(PRStatus.OPEN, 0),
        "risk_alerts":       active_risks,
        "blockers_resolved": 0,
        "active_blockers":   task_counts.get(TaskStatus.BLOCKED, 0),
        "top_contributors":  [],
    }

    # Enrich with sprint data if provided
    if sprint_id:
        sprint_result = await db.execute(select(Sprint).where(Sprint.id == sprint_id))
        sprint = sprint_result.scalar_one_or_none()
        if sprint:
            report_data["points_delivered"] = sprint.points_completed
            report_data["points_planned"]   = sprint.points_planned
            report_data["project_name"]     = f"Sprint: {sprint.name}"

    return await report_service.generate(project_id, report_type, report_data)


@router.get("/velocity/{project_id}")
async def get_velocity_history(
    project_id: int,
    limit:      int        = Query(8, ge=1, le=20),
    db: AsyncSession        = Depends(get_db),
    current_user: User      = Depends(get_current_user),
):
    """Velocity chart data — last N completed sprints."""
    result = await db.execute(
        select(Sprint)
        .where(Sprint.project_id == project_id, Sprint.status == SprintStatus.COMPLETED)
        .order_by(Sprint.end_date.desc())
        .limit(limit)
    )
    sprints = result.scalars().all()
    return [
        {
            "sprint_name":      s.name,
            "points_planned":   s.points_planned,
            "points_completed": s.points_completed,
            "velocity":         s.velocity,
            "health_score":     s.health_score,
        }
        for s in reversed(sprints)
    ]


@router.get("/summary/{project_id}")
async def get_project_summary(
    project_id: int,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Quick stats for the Reports page header cards."""
    task_result = await db.execute(
        select(Task.status, func.count(Task.id))
        .where(Task.project_id == project_id)
        .group_by(Task.status)
    )
    task_counts = {row[0]: row[1] for row in task_result.all()}

    pr_result = await db.execute(
        select(func.count(PullRequest.id))
        .where(PullRequest.project_id == project_id, PullRequest.status == PRStatus.MERGED)
    )
    prs_merged = pr_result.scalar() or 0

    risk_result = await db.execute(
        select(func.count(RiskAlert.id))
        .where(RiskAlert.project_id == project_id, RiskAlert.status == RiskStatus.OPEN)
    )
    open_risks = risk_result.scalar() or 0

    return {
        "total_tasks":     sum(task_counts.values()),
        "completed_tasks": task_counts.get(TaskStatus.DONE, 0),
        "blocked_tasks":   task_counts.get(TaskStatus.BLOCKED, 0),
        "prs_merged":      prs_merged,
        "open_risks":      open_risks,
    }
