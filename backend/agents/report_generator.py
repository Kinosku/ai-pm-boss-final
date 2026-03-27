"""
Report Generator Agent
Generates weekly / sprint / executive reports using LLM,
formats them for Slack, and persists them to DB.
Triggered by scheduler or manual boss action.
"""
import logging
from typing import Any
from datetime import date, timedelta

from sqlalchemy import select, func

from database import AsyncSessionLocal
from models.sprint import Sprint, SprintStatus
from models.task import Task, TaskStatus
from models.pull_request import PullRequest, PRStatus
from models.risk_alert import RiskAlert, RiskStatus
from models.developer import Developer
from services.report_service import report_service, ReportType
from ai.memory import AgentName, save_memory, append_to_history
from core.queue import enqueue_notification

logger = logging.getLogger(__name__)


class ReportGeneratorAgent:
    """
    Agent that:
    1. Collects project/sprint metrics from DB
    2. Calls ReportService (LLM) to generate structured report
    3. Formats for Slack and sends to #dev-team channel
    4. Notifies boss that the report is ready
    """

    name    = AgentName.REPORT_GENERATOR
    display = "Report Generator Agent"

    async def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_id  = payload.get("project_id")
        report_type = payload.get("report_type", "weekly")
        sprint_id   = payload.get("sprint_id")

        logger.info(f"[ReportGeneratorAgent] Running {report_type} report for project={project_id}")

        async with AsyncSessionLocal() as db:
            # 1. Collect metrics
            report_data = await self._collect_metrics(db, project_id, sprint_id)
            report_data["report_type"] = report_type

            # 2. Generate report via LLM
            report = await report_service.generate(project_id, ReportType(report_type), report_data)

            # 3. Format for Slack
            slack_message = report_service.format_for_slack(report)

            # 4. Send to Slack (if integration exists)
            slack_sent = await self._send_to_slack(db, project_id, slack_message)

            # 5. Notify boss
            await enqueue_notification(
                user_id    = project_id,    # replace with actual owner user_id in prod
                message    = f"📊 {report_type.title()} report generated and sent to Slack",
                notif_type = "report_ready",
            )

        # 6. Persist agent memory
        await save_memory(project_id, self.name, {
            "last_report_type":  report_type,
            "last_report_date":  str(date.today()),
            "health_score":      report.get("health_score"),
            "slack_sent":        slack_sent,
        })
        await append_to_history(project_id, self.name, {
            "action":       "report_generated",
            "report_type":  report_type,
            "health_score": report.get("health_score"),
            "slack_sent":   slack_sent,
        })

        logger.info(f"[ReportGeneratorAgent] Report done | Health={report.get('health_score')} | Slack={slack_sent}")
        return {
            "status":       "success",
            "report_type":  report_type,
            "health_score": report.get("health_score"),
            "slack_sent":   slack_sent,
            "summary":      report.get("executive_summary", ""),
        }

    # ─── Metric collection ────────────────────────────────────────────────────
    async def _collect_metrics(
        self, db, project_id: int, sprint_id: int | None
    ) -> dict[str, Any]:
        today = date.today()

        # Task counts
        task_result = await db.execute(
            select(Task.status, func.count(Task.id))
            .where(Task.project_id == project_id)
            .group_by(Task.status)
        )
        task_counts = {row[0]: row[1] for row in task_result.all()}

        # PR counts
        pr_result = await db.execute(
            select(PullRequest.status, func.count(PullRequest.id))
            .where(PullRequest.project_id == project_id)
            .group_by(PullRequest.status)
        )
        pr_counts = {row[0]: row[1] for row in pr_result.all()}

        # Risk alerts
        risk_result = await db.execute(
            select(func.count(RiskAlert.id)).where(
                RiskAlert.project_id == project_id,
                RiskAlert.status     == RiskStatus.OPEN,
            )
        )
        open_risks = risk_result.scalar() or 0

        # Top contributors (by tasks done this week)
        week_ago = today - timedelta(days=7)
        contrib_result = await db.execute(
            select(Task.assigned_to, func.count(Task.id))
            .where(
                Task.project_id == project_id,
                Task.status     == TaskStatus.DONE,
                Task.done_at    >= week_ago,
            )
            .group_by(Task.assigned_to)
            .order_by(func.count(Task.id).desc())
            .limit(3)
        )
        top_contribs = [f"Dev {row[0]} ({row[1]} tasks)" for row in contrib_result.all() if row[0]]

        # Sprint-level data
        points_delivered, points_planned = 0, 0
        if sprint_id:
            sprint_result = await db.execute(select(Sprint).where(Sprint.id == sprint_id))
            sprint = sprint_result.scalar_one_or_none()
            if sprint:
                points_delivered = sprint.points_completed
                points_planned   = sprint.points_planned

        # Developer count
        dev_result = await db.execute(
            select(func.count(Developer.id)).where(Developer.project_id == project_id)
        )
        team_size = dev_result.scalar() or 0

        return {
            "project_name":      f"Project {project_id}",
            "period_start":      str(today - timedelta(days=7)),
            "period_end":        str(today),
            "team_size":         team_size,
            "completed_tasks":   task_counts.get(TaskStatus.DONE, 0),
            "total_tasks":       sum(task_counts.values()),
            "points_delivered":  points_delivered,
            "points_planned":    points_planned,
            "prs_merged":        pr_counts.get(PRStatus.MERGED, 0),
            "prs_open":          pr_counts.get(PRStatus.OPEN, 0),
            "risk_alerts":       open_risks,
            "blockers_resolved": 0,
            "active_blockers":   task_counts.get(TaskStatus.BLOCKED, 0),
            "top_contributors":  top_contribs,
        }

    # ─── Slack sender ─────────────────────────────────────────────────────────
    @staticmethod
    async def _send_to_slack(db, project_id: int, message: str) -> bool:
        """
        Send the report to the project's Slack channel via Slack SDK.
        Returns True if sent, False if integration not configured.
        """
        from models.integration import Integration, IntegrationProvider, IntegrationStatus
        result = await db.execute(
            select(Integration).where(
                Integration.project_id == project_id,
                Integration.provider   == IntegrationProvider.SLACK,
                Integration.status     == IntegrationStatus.CONNECTED,
            )
        )
        integration = result.scalar_one_or_none()
        if not integration or not integration.access_token:
            logger.info("[ReportGeneratorAgent] Slack not connected — skipping send.")
            return False

        try:
            from slack_sdk.web.async_client import AsyncWebClient
            client = AsyncWebClient(token=integration.access_token)
            channel_id = integration.config.get("channel_id", "#dev-team")
            await client.chat_postMessage(channel=channel_id, text=message)
            return True
        except Exception as e:
            logger.error(f"[ReportGeneratorAgent] Slack send failed: {e}")
            return False


# ─── Singleton ───────────────────────────────────────────────────────────────
report_generator_agent = ReportGeneratorAgent()
