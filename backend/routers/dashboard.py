from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from database import get_db
from models.user import User, UserRole
from models.task import Task, TaskStatus
from models.sprint import Sprint, SprintStatus
from models.risk_alert import RiskAlert, RiskStatus, RiskSeverity
from models.pull_request import PullRequest, PRStatus
from models.standup import Standup
from models.developer import Developer
from routers.auth import get_current_user

router = APIRouter()


@router.get("/boss")
async def boss_dashboard(
    project_id: Optional[int] = Query(None),
    db: AsyncSession           = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    """
    Boss Command Center — all the stats for the main dashboard.
    Feeds: open tasks, risk alerts, agent actions count, active sprint health.
    """
    # Active sprint
    sprint_q = select(Sprint).where(Sprint.status == SprintStatus.ACTIVE)
    if project_id:
        sprint_q = sprint_q.where(Sprint.project_id == project_id)
    sprint_result = await db.execute(sprint_q.limit(1))
    active_sprint = sprint_result.scalar_one_or_none()

    # Task counts
    task_q = select(Task.status, func.count(Task.id))
    if project_id:
        task_q = task_q.where(Task.project_id == project_id)
    task_result = await db.execute(task_q.group_by(Task.status))
    task_counts  = {row[0]: row[1] for row in task_result.all()}

    # Risk counts (open)
    risk_q = select(RiskAlert.severity, func.count(RiskAlert.id)).where(
        RiskAlert.status == RiskStatus.OPEN
    )
    if project_id:
        risk_q = risk_q.where(RiskAlert.project_id == project_id)
    risk_result = await db.execute(risk_q.group_by(RiskAlert.severity))
    risk_counts  = {row[0]: row[1] for row in risk_result.all()}

    # Stale PRs
    pr_q = select(func.count(PullRequest.id)).where(
        PullRequest.is_stale == True, PullRequest.status == PRStatus.OPEN
    )
    if project_id:
        pr_q = pr_q.where(PullRequest.project_id == project_id)
    stale_prs = (await db.execute(pr_q)).scalar() or 0

    # Recent risk alerts (top 3 for preview)
    recent_risks_result = await db.execute(
        select(RiskAlert)
        .where(RiskAlert.status == RiskStatus.OPEN)
        .order_by(RiskAlert.created_at.desc())
        .limit(3)
    )
    recent_risks = recent_risks_result.scalars().all()

    # Recent standups (activity feed)
    recent_standups_result = await db.execute(
        select(Standup).where(Standup.is_summary == True)
        .order_by(Standup.created_at.desc()).limit(3)
    )
    recent_standups = recent_standups_result.scalars().all()

    return {
        "active_sprint": {
            "id":               active_sprint.id   if active_sprint else None,
            "name":             active_sprint.name if active_sprint else None,
            "health_score":     active_sprint.health_score if active_sprint else None,
            "points_planned":   active_sprint.points_planned   if active_sprint else 0,
            "points_completed": active_sprint.points_completed if active_sprint else 0,
            "end_date":         str(active_sprint.end_date) if active_sprint and active_sprint.end_date else None,
        },
        "task_counts": {
            "open":        task_counts.get(TaskStatus.TODO, 0) + task_counts.get(TaskStatus.IN_PROGRESS, 0),
            "blocked":     task_counts.get(TaskStatus.BLOCKED, 0),
            "done":        task_counts.get(TaskStatus.DONE, 0),
            "total":       sum(task_counts.values()),
        },
        "risk_counts": {
            "high":        risk_counts.get(RiskSeverity.HIGH, 0) + risk_counts.get(RiskSeverity.CRITICAL, 0),
            "medium":      risk_counts.get(RiskSeverity.MEDIUM, 0),
            "low":         risk_counts.get(RiskSeverity.LOW, 0),
            "total":       sum(risk_counts.values()),
        },
        "stale_prs": stale_prs,
        "recent_risks": [
            {
                "id":          r.id,
                "title":       r.title,
                "severity":    r.severity,
                "detected_by": r.detected_by,
                "created_at":  str(r.created_at),
            }
            for r in recent_risks
        ],
        "activity_feed": [
            {"type": "standup_summary", "text": s.summary_text[:80] if s.summary_text else "", "created_at": str(s.created_at)}
            for s in recent_standups
        ],
    }


@router.get("/employee")
async def employee_dashboard(
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Employee My Work Home — personal tasks, PRs, sprint progress.
    """
    dev_result = await db.execute(
        select(Developer).where(Developer.user_id == current_user.id)
    )
    dev = dev_result.scalar_one_or_none()

    if not dev:
        return {"message": "Developer profile not set up", "tasks": [], "prs": []}

    # My tasks
    tasks_result = await db.execute(
        select(Task)
        .where(Task.assigned_to == dev.id)
        .order_by(Task.priority.desc(), Task.due_date.asc())
        .limit(10)
    )
    my_tasks = tasks_result.scalars().all()

    # My open PRs
    prs_result = await db.execute(
        select(PullRequest)
        .where(PullRequest.author_id == dev.id, PullRequest.status == PRStatus.OPEN)
        .order_by(PullRequest.opened_at.desc())
        .limit(5)
    )
    my_prs = prs_result.scalars().all()

    # Today's standup
    from datetime import date, datetime
    today_start = datetime.combine(date.today(), datetime.min.time())
    standup_result = await db.execute(
        select(Standup).where(
            Standup.developer_id == dev.id,
            Standup.standup_date >= today_start,
            Standup.is_summary   == False,
        ).limit(1)
    )
    today_standup = standup_result.scalar_one_or_none()

    return {
        "developer": {
            "id":         dev.id,
            "role":       dev.role,
            "open_tasks": dev.open_tasks,
            "velocity":   dev.velocity,
        },
        "my_tasks": [
            {
                "id":           t.id,
                "title":        t.title,
                "status":       t.status,
                "priority":     t.priority,
                "story_points": t.story_points,
                "due_date":     str(t.due_date) if t.due_date else None,
            }
            for t in my_tasks
        ],
        "my_prs": [
            {
                "id":               p.id,
                "pr_number":        p.github_pr_number,
                "title":            p.title,
                "status":           p.status,
                "review_status":    p.review_status,
                "is_stale":         p.is_stale,
                "github_url":       p.github_url,
            }
            for p in my_prs
        ],
        "standup_submitted_today": today_standup is not None,
        "task_counts": {
            "todo":        sum(1 for t in my_tasks if t.status == TaskStatus.TODO),
            "in_progress": sum(1 for t in my_tasks if t.status == TaskStatus.IN_PROGRESS),
            "blocked":     sum(1 for t in my_tasks if t.status == TaskStatus.BLOCKED),
            "done":        sum(1 for t in my_tasks if t.status == TaskStatus.DONE),
        },
    }
