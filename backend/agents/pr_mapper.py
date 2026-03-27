"""
PR Mapping Agent
Links GitHub PRs → Jira tasks automatically based on branch names,
PR titles, and commit message conventions (e.g. TASK-042, #42).
"""
import re
import logging
from typing import Any

from sqlalchemy import select

from database import AsyncSessionLocal
from models.pull_request import PullRequest
from models.task import Task
from ai.memory import AgentName, save_memory, append_to_history
from core.queue import enqueue_notification

logger = logging.getLogger(__name__)

# Patterns to detect task references in PR titles / branch names / commit messages
_TASK_REF_PATTERNS = [
    r"TASK[-_](\d+)",          # TASK-042 or TASK_042
    r"#(\d+)",                  # #42
    r"\[(\d+)\]",              # [42]
    r"(?:fix|feat|chore|closes?|refs?)[:\s]+#?(\d+)",  # fix: #42 / closes #42
]


class PRMapperAgent:
    """
    Agent that:
    1. Receives a PR ID
    2. Extracts task references from title + branch name
    3. Looks up matching Task in DB
    4. Links PR → Task (sets task_id on the PR)
    5. Optionally moves linked task to IN_REVIEW status
    """

    name    = AgentName.PR_MAPPER
    display = "PR Mapping Agent"

    async def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        pr_id      = payload.get("pr_id")
        project_id = payload.get("project_id")

        logger.info(f"[PRMapperAgent] Running for pr_id={pr_id} project={project_id}")

        if not pr_id:
            return {"status": "skipped", "reason": "no_pr_id"}

        async with AsyncSessionLocal() as db:
            # 1. Fetch the PR
            pr = await self._get_pr(db, pr_id)
            if not pr:
                logger.warning(f"[PRMapperAgent] PR {pr_id} not found.")
                return {"status": "error", "reason": "pr_not_found"}

            # 2. Extract task references
            refs = self._extract_task_refs(pr.title, pr.head_branch or "")
            if not refs:
                logger.info(f"[PRMapperAgent] No task references found in PR #{pr.github_pr_number}")
                await append_to_history(project_id or pr.project_id, self.name, {
                    "action":    "no_match",
                    "pr_number": pr.github_pr_number,
                    "title":     pr.title,
                })
                return {"status": "no_match", "pr_id": pr_id}

            # 3. Try to match each ref to a Task
            matched_task = None
            for ref in refs:
                task = await self._find_task(db, ref, pr.project_id)
                if task:
                    matched_task = task
                    break

            if not matched_task:
                logger.info(f"[PRMapperAgent] References {refs} found but no DB task matched.")
                return {"status": "no_match", "refs": refs}

            # 4. Link PR → Task
            pr.task_id = matched_task.id
            logger.info(
                f"[PRMapperAgent] Mapped PR #{pr.github_pr_number} → Task {matched_task.id} ({matched_task.title[:40]})"
            )

            # 5. Move task to IN_REVIEW
            from models.task import TaskStatus
            if matched_task.status not in (TaskStatus.IN_REVIEW, TaskStatus.DONE):
                matched_task.status = TaskStatus.IN_REVIEW

            await db.commit()

            # 6. Notify the task assignee
            if matched_task.assigned_to:
                await enqueue_notification(
                    user_id    = matched_task.assigned_to,
                    message    = f"PR #{pr.github_pr_number} '{pr.title}' was mapped to your task.",
                    notif_type = "pr_update",
                )

        await save_memory(project_id or pr.project_id, self.name, {
            "last_pr_mapped":   pr.github_pr_number,
            "last_task_linked": matched_task.id,
        })
        await append_to_history(project_id or pr.project_id, self.name, {
            "action":    "mapped",
            "pr_number": pr.github_pr_number,
            "task_id":   matched_task.id,
            "task_title":matched_task.title[:50],
        })

        return {
            "status":     "success",
            "pr_number":  pr.github_pr_number,
            "task_id":    matched_task.id,
            "task_title": matched_task.title,
        }

    # ─── Ref extraction ───────────────────────────────────────────────────────
    @staticmethod
    def _extract_task_refs(title: str, branch: str) -> list[str]:
        """
        Pull all numeric task references from PR title + branch name.
        Returns a deduplicated list of ref strings like ["42", "TASK-023"].
        """
        refs = []
        text = f"{title} {branch}"

        for pattern in _TASK_REF_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            refs.extend(matches)

        # Also look for full TASK-XXX refs
        full_refs = re.findall(r"TASK[-_](\d+)", text, re.IGNORECASE)
        refs.extend(full_refs)

        return list(dict.fromkeys(refs))   # deduplicate, preserve order

    # ─── DB helpers ───────────────────────────────────────────────────────────
    @staticmethod
    async def _get_pr(db, pr_id: int) -> PullRequest | None:
        result = await db.execute(select(PullRequest).where(PullRequest.id == pr_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def _find_task(db, ref: str, project_id: int) -> Task | None:
        """
        Try to match a ref string to a Task.
        Checks: numeric ID match, jira_key match (TASK-042).
        """
        # Try numeric ID
        if ref.isdigit():
            result = await db.execute(
                select(Task).where(Task.id == int(ref), Task.project_id == project_id)
            )
            task = result.scalar_one_or_none()
            if task:
                return task

        # Try jira_key (e.g. TASK-42 or PROJ-42)
        jira_key = f"TASK-{ref}" if ref.isdigit() else ref.upper()
        result = await db.execute(
            select(Task).where(Task.jira_key == jira_key, Task.project_id == project_id)
        )
        return result.scalar_one_or_none()


# ─── Singleton ───────────────────────────────────────────────────────────────
pr_mapper_agent = PRMapperAgent()
