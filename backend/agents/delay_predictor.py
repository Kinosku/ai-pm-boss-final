"""
Delay Prediction Agent
Monitors sprint velocity, blocked tasks, stale PRs, and inactive devs
→ predicts delays 1–2 weeks early → creates RiskAlerts in DB.
"""
import logging
from typing import Any
from datetime import date, datetime, timedelta

from sqlalchemy import select, func

from database import AsyncSessionLocal
from models.sprint import Sprint, SprintStatus
from models.task import Task, TaskStatus
from models.pull_request import PullRequest, PRStatus
from models.developer import Developer
from models.risk_alert import RiskAlert
from services.risk_engine import risk_engine
from ai.memory import AgentName, save_memory, append_to_history
from core.queue import enqueue_notification

logger = logging.getLogger(__name__)


class DelayPredictorAgent:
    """
    Agent that:
    1. Collects sprint health signals from DB
    2. Runs RiskEngine (heuristics + LLM analysis)
    3. Persists new RiskAlerts
    4. Notifies the boss if critical risks are found
    """

    name    = AgentName.DELAY_PREDICTOR
    display = "Delay Prediction Agent"

    async def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_id = payload.get("project_id")
        sprint_id  = payload.get("sprint_id")

        logger.info(f"[DelayPredictorAgent] Running for project={project_id} sprint={sprint_id}")

        async with AsyncSessionLocal() as db:
            # 1. Fetch sprint
            sprint = await self._get_sprint(db, sprint_id, project_id)
            if not sprint:
                logger.warning("[DelayPredictorAgent] No active sprint found.")
                return {"status": "skipped", "reason": "no_active_sprint"}

            # 2. Gather all sprint signals
            sprint_data = await self._collect_sprint_data(db, sprint)

            # 3. Run risk analysis
            analysis = await risk_engine.analyze(project_id, sprint_data)

            risks      = analysis.get("risks", [])
            health     = analysis.get("sprint_health_score", 50)
            status_str = analysis.get("overall_status", "unknown")

            # 4. Persist new risk alerts (skip duplicates by title)
            existing_titles = await self._get_existing_titles(db, project_id, sprint.id)
            new_alerts = []

            for risk in risks:
                if risk.get("title", "")[:40] in existing_titles:
                    continue
                alert = RiskAlert(
                    project_id          = project_id,
                    sprint_id           = sprint.id,
                    alert_id            = risk.get("id"),
                    title               = risk.get("title", "Unknown Risk"),
                    description         = risk.get("description"),
                    recommendation      = risk.get("recommendation"),
                    severity            = risk.get("severity", "medium"),
                    category            = risk.get("category", "other"),
                    affected_developers = risk.get("affected_developers", []),
                    affected_tasks      = risk.get("affected_tasks", []),
                    detected_by         = self.display,
                    health_score        = health,
                )
                db.add(alert)
                new_alerts.append(alert)

            # 5. Update sprint health score
            sprint.health_score = health
            await db.commit()

            # 6. Notify boss for critical/high risks
            high_risks = [r for r in risks if r.get("severity") in ("critical", "high")]
            if high_risks:
                await enqueue_notification(
                    user_id    = project_id,    # boss user_id (use project owner in prod)
                    message    = f"⚠️ {len(high_risks)} high/critical risks detected in {sprint.name}",
                    notif_type = "risk_alert",
                )

        # 7. Persist memory
        await save_memory(project_id, self.name, {
            "last_sprint_id":  sprint.id,
            "health_score":    health,
            "status":          status_str,
            "new_alerts":      len(new_alerts),
        })
        await append_to_history(project_id, self.name, {
            "action":      "delay_analysis",
            "sprint":      sprint.name,
            "health":      health,
            "new_alerts":  len(new_alerts),
            "high_risks":  len(high_risks),
        })

        logger.info(
            f"[DelayPredictorAgent] Sprint={sprint.name} | Health={health} | "
            f"NewAlerts={len(new_alerts)} | HighRisks={len(high_risks)}"
        )
        return {
            "status":         "success",
            "sprint":         sprint.name,
            "health_score":   health,
            "overall_status": status_str,
            "new_alerts":     len(new_alerts),
            "total_risks":    len(risks),
        }

    # ─── Data collection ─────────────────────────────────────────────────────
    async def _collect_sprint_data(self, db, sprint: Sprint) -> dict[str, Any]:
        project_id = sprint.project_id

        # Task status breakdown
        task_result = await db.execute(
            select(Task.status, func.count(Task.id))
            .where(Task.sprint_id == sprint.id)
            .group_by(Task.status)
        )
        task_counts = {row[0]: row[1] for row in task_result.all()}

        # Previous sprint velocity
        prev_sprint_result = await db.execute(
            select(Sprint)
            .where(
                Sprint.project_id == project_id,
                Sprint.status     == SprintStatus.COMPLETED,
            )
            .order_by(Sprint.end_date.desc())
            .limit(1)
        )
        prev_sprint = prev_sprint_result.scalar_one_or_none()
        last_velocity = prev_sprint.velocity if prev_sprint else 0

        # Stale PRs (open > 48 hours)
        cutoff = datetime.utcnow() - timedelta(hours=48)
        stale_result = await db.execute(
            select(func.count(PullRequest.id)).where(
                PullRequest.project_id == project_id,
                PullRequest.status     == PRStatus.OPEN,
                PullRequest.opened_at  <= cutoff,
            )
        )
        stale_prs = stale_result.scalar() or 0

        # Inactive developers (no commit in 2+ days)
        inactive_cutoff = datetime.utcnow() - timedelta(days=2)
        inactive_result = await db.execute(
            select(func.count(Developer.id)).where(
                Developer.project_id  == project_id,
                Developer.last_commit_at <= inactive_cutoff,
            )
        )
        inactive_devs = inactive_result.scalar() or 0

        return {
            "project_name":      f"Project {project_id}",
            "sprint_name":       sprint.name,
            "sprint_end_date":   str(sprint.end_date.date()) if sprint.end_date else str(date.today() + timedelta(days=7)),
            "total_tasks":       sum(task_counts.values()),
            "completed_tasks":   task_counts.get(TaskStatus.DONE, 0),
            "in_progress_tasks": task_counts.get(TaskStatus.IN_PROGRESS, 0),
            "blocked_tasks":     task_counts.get(TaskStatus.BLOCKED, 0),
            "last_velocity":     last_velocity or 0,
            "current_velocity":  sprint.velocity or 0,
            "stale_prs":         stale_prs,
            "inactive_devs":     inactive_devs,
        }

    # ─── DB helpers ──────────────────────────────────────────────────────────
    @staticmethod
    async def _get_sprint(db, sprint_id: int | None, project_id: int) -> Sprint | None:
        if sprint_id:
            result = await db.execute(select(Sprint).where(Sprint.id == sprint_id))
            return result.scalar_one_or_none()
        # Fall back to active sprint
        result = await db.execute(
            select(Sprint).where(
                Sprint.project_id == project_id,
                Sprint.status     == SprintStatus.ACTIVE,
            ).limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _get_existing_titles(db, project_id: int, sprint_id: int) -> set[str]:
        result = await db.execute(
            select(RiskAlert.title).where(
                RiskAlert.project_id == project_id,
                RiskAlert.sprint_id  == sprint_id,
            )
        )
        return {row[0][:40] for row in result.all()}


# ─── Singleton ───────────────────────────────────────────────────────────────
delay_predictor_agent = DelayPredictorAgent()
