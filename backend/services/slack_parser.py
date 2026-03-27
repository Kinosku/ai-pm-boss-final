"""
Slack Parser Service
Processes incoming Slack messages/events and decides whether
to extract tasks, detect blockers, or log standup updates.
"""
import re
import logging
from typing import Any
from enum import Enum

from services.prd_parser import prd_parser
from ai.memory import AgentName, append_to_history

logger = logging.getLogger(__name__)


# ─── Slack Message Intent ────────────────────────────────────────────────────
class SlackIntent(str, Enum):
    TASK_REQUEST   = "task_request"
    BLOCKER        = "blocker"
    STANDUP_UPDATE = "standup_update"
    GENERAL        = "general"


# ─── Keyword sets ────────────────────────────────────────────────────────────
_TASK_KEYWORDS = {
    "todo", "to-do", "action item", "we need to", "can you",
    "please build", "please create", "please implement", "please fix",
    "assign", "ticket", "task", "create a", "build a", "add a",
    "implement", "fix the", "update the",
}

_BLOCKER_KEYWORDS = {
    "blocked", "blocking", "stuck", "can't proceed", "cannot proceed",
    "waiting on", "need access", "need credentials", "need help",
    "dependency", "escalate",
}

_STANDUP_KEYWORDS = {
    "yesterday i", "today i", "i'm working on", "i am working on",
    "no blockers", "my blocker", "standup", "daily update",
    "done:", "doing:", "blocked:",
}


class SlackParser:
    """
    Parses Slack events and routes them to the appropriate service/agent.
    """

    # ─── Intent Detection ────────────────────────────────────────────────────
    def detect_intent(self, text: str) -> SlackIntent:
        text_lower = text.lower()

        if any(kw in text_lower for kw in _STANDUP_KEYWORDS):
            return SlackIntent.STANDUP_UPDATE

        if any(kw in text_lower for kw in _BLOCKER_KEYWORDS):
            return SlackIntent.BLOCKER

        if any(kw in text_lower for kw in _TASK_KEYWORDS):
            return SlackIntent.TASK_REQUEST

        return SlackIntent.GENERAL

    # ─── Main handler ────────────────────────────────────────────────────────
    async def handle_message(
        self,
        event: dict[str, Any],
        project_id: int,
    ) -> dict[str, Any]:
        """
        Process a raw Slack event payload.
        Returns a result dict with intent + any extracted tasks/blockers.
        """
        text: str = event.get("text", "").strip()
        user: str = event.get("user", "unknown")
        channel: str = event.get("channel", "")
        ts: str = event.get("ts", "")

        if not text:
            return {"intent": SlackIntent.GENERAL, "action": "ignored"}

        # Strip Slack mention formatting <@USERID>
        clean_text = re.sub(r"<@[A-Z0-9]+>", "", text).strip()

        intent = self.detect_intent(clean_text)
        result: dict[str, Any] = {
            "intent": intent,
            "user": user,
            "channel": channel,
            "ts": ts,
            "text": clean_text,
        }

        logger.info(f"[SlackParser] Intent={intent} | User={user} | Project={project_id}")

        if intent == SlackIntent.TASK_REQUEST:
            tasks = await prd_parser.parse(clean_text, project_id, source="slack")
            result["tasks"] = tasks
            result["action"] = "tasks_extracted"

        elif intent == SlackIntent.BLOCKER:
            blocker = self._extract_blocker(clean_text, user)
            result["blocker"] = blocker
            result["action"] = "blocker_detected"

        elif intent == SlackIntent.STANDUP_UPDATE:
            standup = self._parse_standup_message(clean_text, user)
            result["standup"] = standup
            result["action"] = "standup_recorded"

        else:
            result["action"] = "no_action"

        # Persist history
        await append_to_history(project_id, AgentName.STANDUP_BOT, {
            "action": result["action"],
            "intent": intent,
            "user": user,
            "channel": channel,
        })

        return result

    # ─── Blocker extractor ───────────────────────────────────────────────────
    @staticmethod
    def _extract_blocker(text: str, user: str) -> dict[str, Any]:
        return {
            "reporter": user,
            "description": text,
            "severity": "high" if "critical" in text.lower() or "urgent" in text.lower() else "medium",
            "status": "open",
        }

    # ─── Standup message parser ──────────────────────────────────────────────
    @staticmethod
    def _parse_standup_message(text: str, user: str) -> dict[str, Any]:
        """
        Simple heuristic parser for structured standup messages.
        Supports "Done: / Doing: / Blocked:" format.
        """
        done, doing, blocked = [], [], []

        lines = text.splitlines()
        current_section = None

        for line in lines:
            line_lower = line.lower().strip()

            if line_lower.startswith(("done:", "yesterday:")):
                current_section = "done"
                content = line.split(":", 1)[-1].strip()
                if content:
                    done.append(content)

            elif line_lower.startswith(("doing:", "today:", "working on:")):
                current_section = "doing"
                content = line.split(":", 1)[-1].strip()
                if content:
                    doing.append(content)

            elif line_lower.startswith(("blocked:", "blocker:")):
                current_section = "blocked"
                content = line.split(":", 1)[-1].strip()
                if content:
                    blocked.append(content)

            elif line.strip().startswith("-") and current_section:
                item = line.strip().lstrip("-").strip()
                if current_section == "done":
                    done.append(item)
                elif current_section == "doing":
                    doing.append(item)
                elif current_section == "blocked":
                    blocked.append(item)

        return {
            "developer": user,
            "done": done,
            "doing": doing,
            "blocked": blocked,
            "raw": text,
        }

    # ─── Format standup for Slack ────────────────────────────────────────────
    @staticmethod
    def format_for_slack(standup: dict) -> str:
        """Convert a parsed standup dict back into a clean Slack message."""
        lines = [f"*{standup.get('developer', 'Unknown')}*"]
        if standup.get("done"):
            lines.append("✅ Done: " + " | ".join(standup["done"]))
        if standup.get("doing"):
            lines.append("🚀 Doing: " + " | ".join(standup["doing"]))
        if standup.get("blocked"):
            lines.append("🚨 Blocked: " + " | ".join(standup["blocked"]))
        return "\n".join(lines)


# ─── Singleton ───────────────────────────────────────────────────────────────
slack_parser = SlackParser()
