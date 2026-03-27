"""
AI Orchestrator — the central brain of AI PM Boss.
Routes incoming events to the correct agent, manages execution flow,
and persists results back to memory.
"""
from enum import Enum
from typing import Any
import logging

from ai.memory import AgentName, append_to_history
from core.queue import (
    enqueue_task_creation,
    enqueue_pr_mapping,
    enqueue_risk_detection,
    enqueue_report_generation,
    enqueue_standup,
)

logger = logging.getLogger(__name__)


# ─── Event Types ─────────────────────────────────────────────────────────────
class OrchestratorEvent(str, Enum):
    PRD_UPLOADED        = "prd_uploaded"
    SLACK_MESSAGE       = "slack_message"
    GITHUB_PR_OPENED    = "github_pr_opened"
    GITHUB_PR_MERGED    = "github_pr_merged"
    GITHUB_COMMIT       = "github_commit"
    JIRA_TASK_UPDATED   = "jira_task_updated"
    SPRINT_STARTED      = "sprint_started"
    SPRINT_ENDING_SOON  = "sprint_ending_soon"
    DAILY_STANDUP_TIME  = "daily_standup_time"
    WEEKLY_REPORT_TIME  = "weekly_report_time"
    MANUAL_TRIGGER      = "manual_trigger"


# ─── Orchestrator ────────────────────────────────────────────────────────────
class AIOrchestrator:
    """
    Routes events to the appropriate agents via the Redis queue.
    Each agent runs asynchronously as a Celery worker task.
    """

    async def handle_event(
        self,
        event: OrchestratorEvent,
        project_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Main entry point. Receives an event + payload and dispatches
        to the right agent queue(s).
        """
        logger.info(f"[Orchestrator] Event={event} | Project={project_id}")

        result = {"event": event, "project_id": project_id, "dispatched": []}

        # ── PRD uploaded → Task Creator Agent ────────────────────────────────
        if event == OrchestratorEvent.PRD_UPLOADED:
            prd_text = payload.get("prd_text", "")
            await enqueue_task_creation(project_id, prd_text)
            result["dispatched"].append(AgentName.TASK_CREATOR)

        # ── Slack message → Task Creator (if action item detected) ────────────
        elif event == OrchestratorEvent.SLACK_MESSAGE:
            message_text = payload.get("text", "")
            if self._looks_like_task(message_text):
                await enqueue_task_creation(project_id, message_text)
                result["dispatched"].append(AgentName.TASK_CREATOR)

        # ── GitHub PR opened → PR Mapper Agent ───────────────────────────────
        elif event == OrchestratorEvent.GITHUB_PR_OPENED:
            pr_id = payload.get("pr_id")
            await enqueue_pr_mapping(pr_id, project_id)
            result["dispatched"].append(AgentName.PR_MAPPER)

        # ── Sprint events → Risk / Delay Predictor Agent ─────────────────────
        elif event in (
            OrchestratorEvent.SPRINT_ENDING_SOON,
            OrchestratorEvent.GITHUB_COMMIT,
            OrchestratorEvent.JIRA_TASK_UPDATED,
        ):
            sprint_id = payload.get("sprint_id")
            await enqueue_risk_detection(project_id, sprint_id)
            result["dispatched"].append(AgentName.DELAY_PREDICTOR)

        # ── Daily standup time → Standup Bot ─────────────────────────────────
        elif event == OrchestratorEvent.DAILY_STANDUP_TIME:
            channel_id = payload.get("channel_id", "")
            await enqueue_standup(project_id, channel_id)
            result["dispatched"].append(AgentName.STANDUP_BOT)

        # ── Weekly report time → Report Generator Agent ───────────────────────
        elif event == OrchestratorEvent.WEEKLY_REPORT_TIME:
            report_type = payload.get("report_type", "weekly")
            await enqueue_report_generation(project_id, report_type)
            result["dispatched"].append(AgentName.REPORT_GENERATOR)

        # ── Manual trigger → dispatch based on agent name in payload ─────────
        elif event == OrchestratorEvent.MANUAL_TRIGGER:
            await self._handle_manual(project_id, payload, result)

        else:
            logger.warning(f"[Orchestrator] Unhandled event: {event}")

        # Persist to history
        await append_to_history(project_id, "orchestrator", {
            "event": event,
            "dispatched": result["dispatched"],
            "payload_keys": list(payload.keys()),
        })

        return result

    # ─── Manual trigger dispatcher ───────────────────────────────────────────
    async def _handle_manual(
        self,
        project_id: int,
        payload: dict[str, Any],
        result: dict,
    ) -> None:
        agent = payload.get("agent")

        if agent == AgentName.TASK_CREATOR:
            await enqueue_task_creation(project_id, payload.get("prd_text", ""))
            result["dispatched"].append(AgentName.TASK_CREATOR)

        elif agent == AgentName.PR_MAPPER:
            await enqueue_pr_mapping(payload.get("pr_id"), project_id)
            result["dispatched"].append(AgentName.PR_MAPPER)

        elif agent == AgentName.DELAY_PREDICTOR:
            await enqueue_risk_detection(project_id, payload.get("sprint_id"))
            result["dispatched"].append(AgentName.DELAY_PREDICTOR)

        elif agent == AgentName.REPORT_GENERATOR:
            await enqueue_report_generation(project_id, payload.get("report_type", "weekly"))
            result["dispatched"].append(AgentName.REPORT_GENERATOR)

        elif agent == AgentName.STANDUP_BOT:
            await enqueue_standup(project_id, payload.get("channel_id", ""))
            result["dispatched"].append(AgentName.STANDUP_BOT)

        else:
            logger.warning(f"[Orchestrator] Unknown manual agent: {agent}")

    # ─── Heuristic helpers ───────────────────────────────────────────────────
    @staticmethod
    def _looks_like_task(text: str) -> bool:
        """Simple heuristic: check if a Slack message sounds like a task/action item."""
        keywords = [
            "todo", "to-do", "action item", "please", "can you",
            "we need", "fix", "implement", "add", "create", "build",
            "assign", "task", "ticket",
        ]
        text_lower = text.lower()
        return any(kw in text_lower for kw in keywords)


# ─── Singleton ───────────────────────────────────────────────────────────────
orchestrator = AIOrchestrator()
