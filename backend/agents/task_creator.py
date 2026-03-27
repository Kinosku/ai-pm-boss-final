"""
Task Creator Agent
Reads PRDs and Slack messages → auto-creates developer-ready tasks.
Triggered via Celery worker from the Redis queue.
"""
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import AsyncSessionLocal
from models.task import Task
from models.project import Project
from models.developer import Developer
from services.prd_parser import prd_parser
from services.assignment_engine import assignment_engine
from ai.memory import AgentName, save_memory, append_to_history
from core.queue import enqueue_notification

logger = logging.getLogger(__name__)


class TaskCreatorAgent:
    """
    Agent that:
    1. Receives PRD text (or Slack message)
    2. Calls PRDParser → extracts structured tasks
    3. Optionally auto-assigns tasks to developers
    4. Persists tasks to DB
    5. Notifies relevant users
    """

    name    = AgentName.TASK_CREATOR
    display = "Task Creator Agent"

    async def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_id = payload.get("project_id")
        prd_text   = payload.get("prd_text", "")
        source     = payload.get("source", "prd")
        sprint_id  = payload.get("sprint_id")
        auto_assign= payload.get("auto_assign", True)

        logger.info(f"[TaskCreatorAgent] Running for project={project_id} source={source}")

        if not prd_text.strip():
            logger.warning("[TaskCreatorAgent] Empty PRD text — aborting.")
            return {"status": "skipped", "reason": "empty_prd"}

        async with AsyncSessionLocal() as db:
            # 1. Extract tasks via LLM
            extracted = await prd_parser.parse(prd_text, project_id, source)
            if not extracted:
                return {"status": "skipped", "reason": "no_tasks_extracted"}

            # 2. Fetch developers for assignment
            developers = []
            if auto_assign:
                developers = await self._fetch_developers(db, project_id)

            # 3. Assign if we have devs
            if developers:
                dev_dicts  = self._to_dict_list(developers)
                extracted  = assignment_engine.assign_bulk(extracted, dev_dicts)

            # 4. Persist to DB
            created_tasks = []
            for item in extracted:
                task = Task(
                    title               = item.get("title", "Untitled"),
                    description         = item.get("description"),
                    priority            = item.get("priority", "medium"),
                    story_points        = item.get("story_points"),
                    suggested_role      = item.get("suggested_role"),
                    labels              = item.get("labels", []),
                    acceptance_criteria = item.get("acceptance_criteria", []),
                    source              = source,
                    project_id          = project_id,
                    sprint_id           = sprint_id,
                    assigned_to         = item.get("assigned_to"),
                )
                db.add(task)
                created_tasks.append(task)

            await db.flush()

            # 5. Update developer open_tasks counter
            for item in extracted:
                if item.get("assigned_to"):
                    await self._increment_open_tasks(db, item["assigned_to"])

            await db.commit()

            # 6. Notify assigned developers
            for item in extracted:
                if item.get("assigned_to"):
                    await enqueue_notification(
                        user_id    = item["assigned_to"],
                        message    = f"AI Boss assigned you a new task: {item.get('title', '')}",
                        notif_type = "task_assigned",
                    )

        # 7. Persist agent memory
        summary = prd_parser.summarize(extracted)
        await save_memory(project_id, self.name, {
            "last_run_source":  source,
            "tasks_created":    len(created_tasks),
            "total_points":     summary.get("total_story_points", 0),
        })
        await append_to_history(project_id, self.name, {
            "action":        "tasks_created",
            "count":         len(created_tasks),
            "source":        source,
            "auto_assigned": auto_assign and bool(developers),
        })

        logger.info(f"[TaskCreatorAgent] Created {len(created_tasks)} tasks for project={project_id}")
        return {
            "status":        "success",
            "tasks_created": len(created_tasks),
            "summary":       summary,
        }

    # ─── Helpers ──────────────────────────────────────────────────────────────
    @staticmethod
    async def _fetch_developers(db: AsyncSession, project_id: int) -> list[Developer]:
        result = await db.execute(
            select(Developer).where(
                Developer.project_id  == project_id,
                Developer.is_available == True,
            )
        )
        return result.scalars().all()

    @staticmethod
    def _to_dict_list(devs: list[Developer]) -> list[dict]:
        return [
            {
                "id":           d.id,
                "name":         f"Dev {d.id}",
                "role":         d.role,
                "skills":       d.skills or [],
                "open_tasks":   d.open_tasks,
                "velocity":     d.velocity,
                "is_available": d.is_available,
            }
            for d in devs
        ]

    @staticmethod
    async def _increment_open_tasks(db: AsyncSession, developer_id: int) -> None:
        result = await db.execute(select(Developer).where(Developer.id == developer_id))
        dev = result.scalar_one_or_none()
        if dev:
            dev.open_tasks = (dev.open_tasks or 0) + 1


# ─── Singleton ───────────────────────────────────────────────────────────────
task_creator_agent = TaskCreatorAgent()
