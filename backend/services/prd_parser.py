"""
PRD Parser Service
Accepts raw PRD text (pasted or uploaded) and uses the LLM
to extract structured, developer-ready tasks from it.
"""
import logging
from typing import Any

from ai.llm import invoke_llm_json, load_prompt
from ai.memory import AgentName, save_memory, append_to_history

logger = logging.getLogger(__name__)


class PRDParser:
    """
    Parses Product Requirement Documents into actionable task lists.
    Supports plain text PRDs as well as Slack-style feature requests.
    """

    def __init__(self):
        self._prompt: str | None = None

    def _get_prompt(self) -> str:
        if self._prompt is None:
            self._prompt = load_prompt("task_prompt.txt")
        return self._prompt

    # ─── Main parse method ───────────────────────────────────────────────────
    async def parse(
        self,
        prd_text: str,
        project_id: int,
        source: str = "prd",          # "prd" | "slack" | "manual"
    ) -> list[dict[str, Any]]:
        """
        Parse PRD or message text into a list of task dicts.

        Returns a list like:
        [
          {
            "title": "...",
            "description": "...",
            "priority": "high|medium|low",
            "story_points": 3,
            "suggested_role": "backend|frontend|fullstack|devops",
            "labels": [...],
            "acceptance_criteria": [...]
          },
          ...
        ]
        """
        if not prd_text or not prd_text.strip():
            logger.warning("[PRDParser] Empty input — returning no tasks.")
            return []

        system_prompt = self._get_prompt()

        user_message = (
            f"Source type: {source.upper()}\n\n"
            f"--- BEGIN INPUT ---\n{prd_text.strip()}\n--- END INPUT ---"
        )

        logger.info(f"[PRDParser] Parsing {source} for project {project_id} ...")

        try:
            tasks = await invoke_llm_json(system_prompt, user_message)
        except ValueError as e:
            logger.error(f"[PRDParser] LLM parse error: {e}")
            return []

        if not isinstance(tasks, list):
            logger.error("[PRDParser] LLM returned non-list JSON — aborting.")
            return []

        # Attach metadata
        for i, task in enumerate(tasks):
            task["source"] = source
            task["project_id"] = project_id
            task["order"] = i + 1

        # Persist to agent memory
        await save_memory(project_id, AgentName.TASK_CREATOR, {
            "last_parse_source": source,
            "tasks_extracted": len(tasks),
        })
        await append_to_history(project_id, AgentName.TASK_CREATOR, {
            "action": "parsed_prd",
            "source": source,
            "tasks_count": len(tasks),
        })

        logger.info(f"[PRDParser] Extracted {len(tasks)} tasks from {source}.")
        return tasks

    # ─── Quick stats ─────────────────────────────────────────────────────────
    @staticmethod
    def summarize(tasks: list[dict]) -> dict[str, Any]:
        """Return a quick summary dict of extracted tasks."""
        priorities = {"high": 0, "medium": 0, "low": 0}
        total_points = 0

        for task in tasks:
            p = task.get("priority", "medium").lower()
            if p in priorities:
                priorities[p] += 1
            total_points += task.get("story_points", 0)

        return {
            "total_tasks": len(tasks),
            "total_story_points": total_points,
            "by_priority": priorities,
        }


# ─── Singleton ───────────────────────────────────────────────────────────────
prd_parser = PRDParser()
