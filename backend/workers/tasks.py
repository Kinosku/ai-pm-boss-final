"""
Celery Tasks
Each function is a Celery task that wraps an AI agent's async run() method.
Tasks are dispatched by the orchestrator via Redis queue.
"""
import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import select

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run(coro):
    """Run an async coroutine from a sync Celery task."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ─── Agent tasks ─────────────────────────────────────────────────────────────

@celery_app.task(bind=True, name="workers.tasks.run_task_creator", max_retries=3)
def run_task_creator(self, payload: dict):
    """Celery task: Task Creator Agent."""
    try:
        from agents.task_creator import task_creator_agent
        result = _run(task_creator_agent.run(payload))
        logger.info(f"[TaskCreator] Done: {result}")
        return result
    except Exception as exc:
        logger.error(f"[TaskCreator] Error: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, name="workers.tasks.run_pr_mapper", max_retries=3)
def run_pr_mapper(self, payload: dict):
    """Celery task: PR Mapper Agent."""
    try:
        from agents.pr_mapper import pr_mapper_agent
        result = _run(pr_mapper_agent.run(payload))
        logger.info(f"[PRMapper] Done: {result}")
        return result
    except Exception as exc:
        logger.error(f"[PRMapper] Error: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, name="workers.tasks.run_delay_predictor", max_retries=3)
def run_delay_predictor(self, payload: dict):
    """Celery task: Delay Predictor Agent."""
    try:
        from agents.delay_predictor import delay_predictor_agent
        result = _run(delay_predictor_agent.run(payload))
        logger.info(f"[DelayPredictor] Done: {result}")
        return result
    except Exception as exc:
        logger.error(f"[DelayPredictor] Error: {exc}")
        raise self.retry(exc=exc, countdown=120)


@celery_app.task(bind=True, name="workers.tasks.run_report_generator", max_retries=2)
def run_report_generator(self, payload: dict):
    """Celery task: Report Generator Agent."""
    try:
        from agents.report_generator import report_generator_agent
        result = _run(report_generator_agent.run(payload))
        logger.info(f"[ReportGenerator] Done: {result}")
        return result
    except Exception as exc:
        logger.error(f"[ReportGenerator] Error: {exc}")
        raise self.retry(exc=exc, countdown=120)


@celery_app.task(bind=True, name="workers.tasks.run_standup_bot", max_retries=2)
def run_standup_bot(self, payload: dict):
    """Celery task: Standup Bot Agent."""
    try:
        from agents.standup_bot import standup_bot_agent
        result = _run(standup_bot_agent.run(payload))
        logger.info(f"[StandupBot] Done: {result}")
        return result
    except Exception as exc:
        logger.error(f"[StandupBot] Error: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="workers.tasks.send_notification")
def send_notification(payload: dict):
    """Celery task: persist a notification to the DB."""
    try:
        from database import AsyncSessionLocal
        from models.notification import Notification

        async def _save():
            async with AsyncSessionLocal() as db:
                notif = Notification(
                    user_id     = payload.get("user_id"),
                    type        = payload.get("type", "system"),
                    title       = payload.get("message", "New notification"),
                    message     = payload.get("message"),
                    source_type = payload.get("notif_type"),
                )
                db.add(notif)
                await db.commit()

        _run(_save())
        return {"status": "sent"}
    except Exception as exc:
        logger.error(f"[Notification] Error: {exc}")
        return {"status": "error", "error": str(exc)}


# ─── Scheduled / periodic tasks ───────────────────────────────────────────────

@celery_app.task(name="workers.tasks.scheduled_standup")
def scheduled_standup():
    """Beat task: trigger standup bot for all active projects."""
    async def _run_all():
        from database import AsyncSessionLocal
        from models.project import Project, ProjectStatus
        from models.integration import Integration, IntegrationProvider, IntegrationStatus
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            projects_result = await db.execute(
                select(Project).where(Project.status == ProjectStatus.ACTIVE)
            )
            projects = projects_result.scalars().all()

            for project in projects:
                intg_result = await db.execute(
                    select(Integration).where(
                        Integration.project_id == project.id,
                        Integration.provider   == IntegrationProvider.SLACK,
                        Integration.status     == IntegrationStatus.CONNECTED,
                    )
                )
                intg = intg_result.scalar_one_or_none()
                channel_id = intg.config.get("channel_id", "") if intg else ""

                run_standup_bot.delay({
                    "project_id": project.id,
                    "channel_id": channel_id,
                })
                logger.info(f"[Beat] Standup queued for project {project.id}")

    _run(_run_all())


@celery_app.task(name="workers.tasks.scheduled_weekly_report")
def scheduled_weekly_report():
    """Beat task: generate weekly report for all active projects."""
    async def _run_all():
        from database import AsyncSessionLocal
        from models.project import Project, ProjectStatus

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Project).where(Project.status == ProjectStatus.ACTIVE)
            )
            projects = result.scalars().all()
            for project in projects:
                run_report_generator.delay({
                    "project_id":  project.id,
                    "report_type": "weekly",
                })
                logger.info(f"[Beat] Weekly report queued for project {project.id}")

    _run(_run_all())


@celery_app.task(name="workers.tasks.scheduled_risk_check")
def scheduled_risk_check():
    """Beat task: run delay predictor for all active sprints."""
    async def _run_all():
        from database import AsyncSessionLocal
        from models.sprint import Sprint, SprintStatus

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Sprint).where(Sprint.status == SprintStatus.ACTIVE)
            )
            sprints = result.scalars().all()
            for sprint in sprints:
                run_delay_predictor.delay({
                    "project_id": sprint.project_id,
                    "sprint_id":  sprint.id,
                })
                logger.info(f"[Beat] Risk check queued for sprint {sprint.id}")

    _run(_run_all())


@celery_app.task(name="workers.tasks.mark_stale_pull_requests")
def mark_stale_pull_requests():
    """Beat task: mark PRs open > 48 hours as stale."""
    async def _mark():
        from database import AsyncSessionLocal
        from models.pull_request import PullRequest, PRStatus

        cutoff = datetime.utcnow() - timedelta(hours=48)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(PullRequest).where(
                    PullRequest.status    == PRStatus.OPEN,
                    PullRequest.is_stale  == False,
                    PullRequest.opened_at <= cutoff,
                )
            )
            prs = result.scalars().all()
            for pr in prs:
                pr.is_stale = True
            await db.commit()
            logger.info(f"[Beat] Marked {len(prs)} PRs as stale")

    _run(_mark())
