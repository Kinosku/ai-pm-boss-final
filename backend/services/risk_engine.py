"""
Risk Engine Service
Analyzes sprint health data and calls the LLM risk prompt
to produce structured risk alerts with severity scoring.
Mirrors the UI: High / Medium / Low risk cards with velocity,
PR bottleneck, and blocker detection.
"""
import logging
from typing import Any
from datetime import date, datetime

from ai.llm import invoke_llm_json, load_prompt
from ai.memory import AgentName, save_memory, append_to_history

logger = logging.getLogger(__name__)


class RiskEngine:
    """
    Detects project risks by combining rule-based heuristics
    with LLM-powered analysis.
    """

    def __init__(self):
        self._prompt: str | None = None

    def _get_prompt(self) -> str:
        if self._prompt is None:
            self._prompt = load_prompt("risk_prompt.txt")
        return self._prompt

    # ─── Main analyze method ─────────────────────────────────────────────────
    async def analyze(
        self,
        project_id: int,
        sprint_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Full risk analysis pipeline:
        1. Run rule-based fast checks.
        2. Call LLM for deep analysis.
        3. Merge results and return.

        sprint_data keys expected:
          project_name, sprint_name, sprint_end_date,
          total_tasks, completed_tasks, in_progress_tasks, blocked_tasks,
          last_velocity, current_velocity, stale_prs, inactive_devs,
          developers (list of dev dicts)
        """
        logger.info(f"[RiskEngine] Analyzing project {project_id} ...")

        # Fast heuristic risks (no LLM needed)
        fast_risks = self._fast_check(sprint_data)

        # Days remaining
        sprint_end = sprint_data.get("sprint_end_date")
        days_remaining = self._days_remaining(sprint_end)

        # Build context for prompt
        context = {
            "project_name":       sprint_data.get("project_name", "Unknown"),
            "sprint_name":        sprint_data.get("sprint_name", "Current Sprint"),
            "sprint_end_date":    str(sprint_end),
            "days_remaining":     days_remaining,
            "total_tasks":        sprint_data.get("total_tasks", 0),
            "completed_tasks":    sprint_data.get("completed_tasks", 0),
            "in_progress_tasks":  sprint_data.get("in_progress_tasks", 0),
            "blocked_tasks":      sprint_data.get("blocked_tasks", 0),
            "last_velocity":      sprint_data.get("last_velocity", 0),
            "current_velocity":   sprint_data.get("current_velocity", 0),
            "stale_prs":          sprint_data.get("stale_prs", 0),
            "inactive_devs":      sprint_data.get("inactive_devs", 0),
        }

        user_message = (
            f"Analyze the sprint health for project '{context['project_name']}'. "
            f"Sprint ends in {days_remaining} days. "
            f"Velocity dropped from {context['last_velocity']} to {context['current_velocity']} points. "
            f"There are {context['blocked_tasks']} blocked tasks and {context['stale_prs']} stale PRs."
        )

        try:
            llm_result = await invoke_llm_json(
                self._get_prompt().format(**context),
                user_message,
            )
        except Exception as e:
            logger.error(f"[RiskEngine] LLM error: {e}")
            llm_result = {
                "sprint_health_score": 50,
                "overall_status": "unknown",
                "risks": [],
                "summary": "AI analysis unavailable.",
            }

        # Merge fast risks into LLM risks list
        all_risks = fast_risks + llm_result.get("risks", [])
        llm_result["risks"] = all_risks

        # Deduplicate by title similarity (simple)
        llm_result["risks"] = self._deduplicate(llm_result["risks"])

        # Persist
        await save_memory(project_id, AgentName.DELAY_PREDICTOR, {
            "last_health_score": llm_result.get("sprint_health_score"),
            "last_status":       llm_result.get("overall_status"),
            "risk_count":        len(llm_result["risks"]),
        })
        await append_to_history(project_id, AgentName.DELAY_PREDICTOR, {
            "action":       "risk_analysis",
            "health_score": llm_result.get("sprint_health_score"),
            "risk_count":   len(llm_result["risks"]),
        })

        logger.info(
            f"[RiskEngine] Health={llm_result.get('sprint_health_score')} | "
            f"Risks={len(llm_result['risks'])}"
        )
        return llm_result

    # ─── Rule-based fast checks ──────────────────────────────────────────────
    def _fast_check(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Instant heuristic risk checks that don't need the LLM."""
        risks = []

        # Velocity drop > 30%
        last_v    = data.get("last_velocity", 0)
        current_v = data.get("current_velocity", 0)
        if last_v > 0 and current_v < last_v * 0.7:
            drop_pct = round((1 - current_v / last_v) * 100)
            risks.append({
                "id":           "FAST-001",
                "title":        f"Sprint velocity down {drop_pct}% — delay predicted",
                "category":     "velocity",
                "severity":     "high" if drop_pct > 40 else "medium",
                "description":  (
                    f"Current velocity: {current_v} pts/day. "
                    f"Required: {last_v} pts/day. "
                    f"Detected by Delay Prediction Agent."
                ),
                "recommendation": "Hold a sync to identify blockers. Re-estimate remaining tasks.",
                "affected_developers": [],
                "affected_tasks": [],
            })

        # Stale PRs
        stale_prs = data.get("stale_prs", 0)
        if stale_prs >= 3:
            risks.append({
                "id":           "FAST-002",
                "title":        f"{stale_prs} PRs unreviewed for 5+ days — blocking sprint completion",
                "category":     "pr_bottleneck",
                "severity":     "high" if stale_prs >= 5 else "medium",
                "description":  "Unreviewed PRs are blocking dependent tasks from starting.",
                "recommendation": "Schedule a 30-min PR review session. Assign reviewers explicitly.",
                "affected_developers": [],
                "affected_tasks": [],
            })

        # Blocked tasks > 20% of total
        total    = data.get("total_tasks", 1)
        blocked  = data.get("blocked_tasks", 0)
        if total > 0 and (blocked / total) > 0.2:
            risks.append({
                "id":           "FAST-003",
                "title":        f"{blocked} tasks blocked — over 20% of sprint scope",
                "category":     "blockers",
                "severity":     "high",
                "description":  "High ratio of blocked tasks will prevent sprint completion.",
                "recommendation": "Identify and resolve top 3 blockers in today's standup.",
                "affected_developers": [],
                "affected_tasks": [],
            })

        # Inactive developers
        inactive = data.get("inactive_devs", 0)
        if inactive >= 2:
            risks.append({
                "id":           "FAST-004",
                "title":        f"{inactive} developers with no commits in 2+ days",
                "category":     "team",
                "severity":     "medium",
                "description":  "Inactive developers may be stuck, off-track, or blocked.",
                "recommendation": "Reach out directly via Slack to check status.",
                "affected_developers": [],
                "affected_tasks": [],
            })

        return risks

    # ─── Helpers ─────────────────────────────────────────────────────────────
    @staticmethod
    def _days_remaining(sprint_end: Any) -> int:
        if not sprint_end:
            return 0
        if isinstance(sprint_end, str):
            try:
                sprint_end = date.fromisoformat(sprint_end)
            except ValueError:
                return 0
        if isinstance(sprint_end, datetime):
            sprint_end = sprint_end.date()
        delta = sprint_end - date.today()
        return max(delta.days, 0)

    @staticmethod
    def _deduplicate(risks: list[dict]) -> list[dict]:
        """Remove near-duplicate risks by title prefix (first 30 chars)."""
        seen = set()
        unique = []
        for risk in risks:
            key = risk.get("title", "")[:30].lower()
            if key not in seen:
                seen.add(key)
                unique.append(risk)
        return unique

    # ─── Severity counts (for dashboard) ─────────────────────────────────────
    @staticmethod
    def count_by_severity(risks: list[dict]) -> dict[str, int]:
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for r in risks:
            sev = r.get("severity", "low").lower()
            if sev in counts:
                counts[sev] += 1
        return counts


# ─── Singleton ───────────────────────────────────────────────────────────────
risk_engine = RiskEngine()
