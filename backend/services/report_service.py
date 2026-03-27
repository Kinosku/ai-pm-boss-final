"""
Report Service
Generates weekly, sprint, and executive reports using LLM.
Sends generated reports to Slack and stores them in the DB.
Mirrors the Reports & Analytics page: velocity charts, report table,
AI-generated summaries sent to #dev-team Slack channel.
"""
import logging
from typing import Any
from datetime import date, timedelta
from enum import Enum

from ai.llm import invoke_llm_json, load_prompt
from ai.memory import AgentName, save_memory, append_to_history

logger = logging.getLogger(__name__)


# ─── Report Types ────────────────────────────────────────────────────────────
class ReportType(str, Enum):
    WEEKLY      = "weekly"
    SPRINT      = "sprint"
    EXECUTIVE   = "executive"
    RISK        = "risk"


class ReportService:
    """
    Orchestrates report generation:
    1. Assembles sprint/project data
    2. Calls LLM with report prompt
    3. Returns structured report dict ready for storage + Slack delivery
    """

    def __init__(self):
        self._prompt: str | None = None

    def _get_prompt(self) -> str:
        if self._prompt is None:
            self._prompt = load_prompt("report_prompt.txt")
        return self._prompt

    # ─── Main generate method ─────────────────────────────────────────────────
    async def generate(
        self,
        project_id: int,
        report_type: ReportType | str,
        report_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate a report for a project.

        report_data keys expected:
          project_name, team_size,
          period_start, period_end,
          completed_tasks, total_tasks,
          points_delivered, points_planned,
          prs_merged, prs_open,
          risk_alerts, blockers_resolved, active_blockers,
          top_contributors (list of str)
        """
        logger.info(f"[ReportService] Generating {report_type} report for project {project_id}")

        report_type = ReportType(report_type) if isinstance(report_type, str) else report_type

        # Fill defaults
        today = date.today()
        report_data.setdefault("period_start", str(today - timedelta(days=7)))
        report_data.setdefault("period_end",   str(today))
        report_data.setdefault("report_type",  report_type.value)
        report_data.setdefault("team_size",    0)
        report_data.setdefault("top_contributors", [])

        context = {
            "project_name":       report_data.get("project_name", "Unknown"),
            "report_type":        report_type.value,
            "period_start":       report_data.get("period_start"),
            "period_end":         report_data.get("period_end"),
            "team_size":          report_data.get("team_size"),
            "completed_tasks":    report_data.get("completed_tasks", 0),
            "total_tasks":        report_data.get("total_tasks", 0),
            "points_delivered":   report_data.get("points_delivered", 0),
            "points_planned":     report_data.get("points_planned", 0),
            "prs_merged":         report_data.get("prs_merged", 0),
            "prs_open":           report_data.get("prs_open", 0),
            "risk_alerts":        report_data.get("risk_alerts", 0),
            "blockers_resolved":  report_data.get("blockers_resolved", 0),
            "active_blockers":    report_data.get("active_blockers", 0),
            "top_contributors":   ", ".join(report_data.get("top_contributors", [])),
        }

        user_message = (
            f"Generate a {report_type.value} report for project '{context['project_name']}'. "
            f"Period: {context['period_start']} to {context['period_end']}. "
            f"Delivered {context['points_delivered']} of {context['points_planned']} story points. "
            f"Completed {context['completed_tasks']} of {context['total_tasks']} tasks. "
            f"Merged {context['prs_merged']} PRs. Active blockers: {context['active_blockers']}."
        )

        try:
            result = await invoke_llm_json(
                self._get_prompt().format(**context),
                user_message,
            )
        except Exception as e:
            logger.error(f"[ReportService] LLM error: {e}")
            result = self._fallback_report(context)

        # Enrich result
        result["project_id"]   = project_id
        result["report_type"]  = report_type.value
        result["generated_at"] = str(date.today())
        result["generated_by"] = "Report Generator Agent"

        # Persist
        await save_memory(project_id, AgentName.REPORT_GENERATOR, {
            "last_report_type":  report_type.value,
            "last_report_date":  str(today),
            "health_score":      result.get("health_score"),
        })
        await append_to_history(project_id, AgentName.REPORT_GENERATOR, {
            "action":      "report_generated",
            "report_type": report_type.value,
            "period":      f"{context['period_start']} → {context['period_end']}",
        })

        logger.info(f"[ReportService] Report generated. Health={result.get('health_score')}")
        return result

    # ─── Slack formatter ─────────────────────────────────────────────────────
    @staticmethod
    def format_for_slack(report: dict[str, Any]) -> str:
        """
        Convert a report dict into a Slack-ready message.
        Matches the style seen in boss dashboard: sent to #dev-team.
        """
        lines = [
            f"📊 *{report.get('report_type', 'Report').title()} Report* | "
            f"{report.get('period', '')}",
            "",
            f"_{report.get('executive_summary', '')}_",
            "",
        ]

        achievements = report.get("key_achievements", [])
        if achievements:
            lines.append("*✅ Key Achievements*")
            for a in achievements:
                lines.append(f"  • {a}")
            lines.append("")

        risks = report.get("risks_and_blockers", [])
        if risks:
            lines.append("*🚨 Risks & Blockers*")
            for r in risks:
                sev_emoji = "🔴" if r.get("severity") == "high" else "🟡"
                lines.append(f"  {sev_emoji} {r.get('title')} — {r.get('action', '')}")
            lines.append("")

        priorities = report.get("next_period_priorities", [])
        if priorities:
            lines.append("*🚀 Next Period Priorities*")
            for p in priorities:
                lines.append(f"  • {p}")
            lines.append("")

        health = report.get("health_score")
        if health is not None:
            bar = "█" * (health // 10) + "░" * (10 - health // 10)
            lines.append(f"*Sprint Health:* [{bar}] {health}/100")

        lines.append(f"\n_Generated by Report Generator Agent_")
        return "\n".join(lines)

    # ─── Velocity trend calculator ────────────────────────────────────────────
    @staticmethod
    def velocity_trend(sprint_velocities: list[int]) -> str:
        """
        Given a list of sprint story points (oldest → newest),
        return 'improving' | 'stable' | 'declining'.
        """
        if len(sprint_velocities) < 2:
            return "stable"
        recent   = sprint_velocities[-3:]
        avg_old  = sum(sprint_velocities[:-3]) / max(len(sprint_velocities[:-3]), 1)
        avg_new  = sum(recent) / len(recent)
        if avg_new > avg_old * 1.1:
            return "improving"
        if avg_new < avg_old * 0.9:
            return "declining"
        return "stable"

    # ─── Fallback report ─────────────────────────────────────────────────────
    @staticmethod
    def _fallback_report(context: dict) -> dict:
        """Minimal report when LLM is unavailable."""
        return {
            "executive_summary":      f"Report for {context['project_name']} ({context['period_start']} – {context['period_end']}). AI analysis unavailable.",
            "key_achievements":       [],
            "risks_and_blockers":     [],
            "team_performance":       {"velocity_trend": "unknown", "top_performers": [], "notes": ""},
            "next_period_priorities": [],
            "health_score":           None,
            "recommendation":         "Review project data manually.",
        }


# ─── Singleton ───────────────────────────────────────────────────────────────
report_service = ReportService()
