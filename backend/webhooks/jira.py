"""
Jira Webhook Handler
Receives Jira issue events (created, updated, status changed, sprint events)
→ syncs Task/Sprint state in DB → triggers orchestrator when needed.
"""
import logging
from typing import Any

from fastapi import APIRouter, Request, HTTPException, Header
from sqlalchemy import select

from database import AsyncSessionLocal
from models.task import Task, TaskStatus
from models.sprint import Sprint, SprintStatus
from models.integration import Integration, IntegrationProvider, IntegrationStatus
from ai.orchestrator import orchestrator, OrchestratorEvent

router = APIRouter()
logger = logging.getLogger(__name__)


# ─── Jira status → TaskStatus map ────────────────────────────────────────────
JIRA_STATUS_MAP: dict[str, TaskStatus] = {
    "to do":        TaskStatus.TODO,
    "backlog":      TaskStatus.BACKLOG,
    "in progress":  TaskStatus.IN_PROGRESS,
    "in review":    TaskStatus.IN_REVIEW,
    "blocked":      TaskStatus.BLOCKED,
    "done":         TaskStatus.DONE,
    "closed":       TaskStatus.DONE,
    "resolved":     TaskStatus.DONE,
}

JIRA_PRIORITY_MAP = {
    "highest": "high",
    "high":    "high",
    "medium":  "medium",
    "low":     "low",
    "lowest":  "low",
}


# ─── Project resolver ─────────────────────────────────────────────────────────
async def _resolve_project(jira_project_key: str) -> int | None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Integration).where(
                Integration.provider == IntegrationProvider.JIRA,
                Integration.status   == IntegrationStatus.CONNECTED,
            )
        )
        integrations = result.scalars().all()
        for intg in integrations:
            if intg.config.get("project_key") == jira_project_key:
                return intg.project_id
    return None


# ─── Simple token auth (Jira sends a secret in header or query) ───────────────
def _verify_jira_token(authorization: str | None) -> bool:
    # In production, compare against a stored webhook token
    # For now, just check it's present
    return True


# ─── Main webhook endpoint ────────────────────────────────────────────────────
@router.post("/")
async def jira_webhook(
    request:       Request,
    authorization: str | None = Header(None),
):
    if not _verify_jira_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid Jira webhook token")

    payload: dict[str, Any] = await request.json()
    webhook_event = payload.get("webhookEvent", "")

    logger.info(f"[JiraWebhook] Event={webhook_event}")

    # ── Issue events ──────────────────────────────────────────────────────────
    if webhook_event in (
        "jira:issue_created",
        "jira:issue_updated",
        "jira:issue_deleted",
    ):
        await _handle_issue_event(webhook_event, payload)

    # ── Sprint events ─────────────────────────────────────────────────────────
    elif webhook_event in (
        "sprint_created",
        "sprint_started",
        "sprint_closed",
        "sprint_updated",
    ):
        await _handle_sprint_event(webhook_event, payload)

    # ── Comment events ────────────────────────────────────────────────────────
    elif webhook_event == "comment_created":
        await _handle_comment(payload)

    else:
        logger.debug(f"[JiraWebhook] Unhandled event: {webhook_event}")

    return {"status": "received", "event": webhook_event}


# ─── Issue handler ────────────────────────────────────────────────────────────
async def _handle_issue_event(event: str, payload: dict[str, Any]) -> None:
    issue       = payload.get("issue", {})
    fields      = issue.get("fields", {})
    jira_key    = issue.get("key", "")               # e.g. "PROJ-42"
    project_key = jira_key.split("-")[0] if "-" in jira_key else ""

    project_id = await _resolve_project(project_key)
    if not project_id:
        logger.warning(f"[JiraWebhook] No project mapped to Jira key: {project_key}")
        return

    # ── Created ───────────────────────────────────────────────────────────────
    if event == "jira:issue_created":
        jira_status   = fields.get("status", {}).get("name", "to do").lower()
        jira_priority = fields.get("priority", {}).get("name", "medium").lower()
        story_points  = fields.get("story_points") or fields.get("customfield_10016")

        async with AsyncSessionLocal() as db:
            # Check if we already have this task (created by AI first)
            existing = await db.execute(
                select(Task).where(Task.jira_key == jira_key)
            )
            if existing.scalar_one_or_none():
                logger.info(f"[JiraWebhook] Task {jira_key} already exists — skipping.")
                return

            task = Task(
                title        = fields.get("summary", "Untitled"),
                description  = fields.get("description", ""),
                status       = JIRA_STATUS_MAP.get(jira_status, TaskStatus.TODO),
                priority     = JIRA_PRIORITY_MAP.get(jira_priority, "medium"),
                story_points = int(story_points) if story_points else None,
                jira_key     = jira_key,
                jira_url     = f"{payload.get('issue', {}).get('self', '')}",
                project_id   = project_id,
                source       = "jira",
            )
            db.add(task)
            await db.commit()
            logger.info(f"[JiraWebhook] Created task from Jira issue {jira_key}")

    # ── Updated ───────────────────────────────────────────────────────────────
    elif event == "jira:issue_updated":
        changelog   = payload.get("changelog", {})
        change_items= changelog.get("items", [])

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Task).where(Task.jira_key == jira_key))
            task   = result.scalar_one_or_none()
            if not task:
                return

            changed = False
            for item in change_items:
                field = item.get("field", "").lower()

                if field == "status":
                    new_status = item.get("toString", "").lower()
                    mapped     = JIRA_STATUS_MAP.get(new_status)
                    if mapped:
                        task.status = mapped
                        changed = True

                elif field == "assignee":
                    # Look up developer by Jira account ID
                    assignee_id = payload.get("issue", {}).get("fields", {}).get("assignee", {}).get("accountId")
                    if assignee_id:
                        dev_result = await db.execute(
                            select(Task).where(Task.jira_key == jira_key)
                        )
                        # TODO: Map Jira accountId → Developer in full impl

                elif field == "story points" or field == "story_points":
                    new_val = item.get("toString")
                    if new_val:
                        try:
                            task.story_points = int(float(new_val))
                            changed = True
                        except (ValueError, TypeError):
                            pass

            if changed:
                await db.commit()
                logger.info(f"[JiraWebhook] Updated task {jira_key}")

                # Trigger risk detection on task update
                await orchestrator.handle_event(
                    OrchestratorEvent.JIRA_TASK_UPDATED,
                    project_id,
                    {"jira_key": jira_key, "sprint_id": task.sprint_id},
                )

    # ── Deleted ───────────────────────────────────────────────────────────────
    elif event == "jira:issue_deleted":
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Task).where(Task.jira_key == jira_key))
            task   = result.scalar_one_or_none()
            if task:
                await db.delete(task)
                await db.commit()
                logger.info(f"[JiraWebhook] Deleted task {jira_key}")


# ─── Sprint handler ───────────────────────────────────────────────────────────
async def _handle_sprint_event(event: str, payload: dict[str, Any]) -> None:
    sprint_data = payload.get("sprint", {})
    jira_sprint_id = str(sprint_data.get("id", ""))
    project_key    = sprint_data.get("originBoardId", "")

    # Try resolving project from board — simplified here
    # In full impl, map board ID → project via integration config

    if event == "sprint_started":
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Sprint).where(Sprint.jira_sprint_id == jira_sprint_id)
            )
            sprint = result.scalar_one_or_none()
            if sprint:
                sprint.status = SprintStatus.ACTIVE
                await db.commit()

        # Trigger orchestrator
        logger.info(f"[JiraWebhook] Sprint {jira_sprint_id} started")

    elif event == "sprint_closed":
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Sprint).where(Sprint.jira_sprint_id == jira_sprint_id)
            )
            sprint = result.scalar_one_or_none()
            if sprint:
                sprint.status = SprintStatus.COMPLETED
                await db.commit()

                # Trigger weekly report
                await orchestrator.handle_event(
                    OrchestratorEvent.WEEKLY_REPORT_TIME,
                    sprint.project_id,
                    {"report_type": "sprint", "sprint_id": sprint.id},
                )
        logger.info(f"[JiraWebhook] Sprint {jira_sprint_id} closed")

    elif event == "sprint_created":
        logger.info(f"[JiraWebhook] Sprint {jira_sprint_id} created in Jira")

    elif event == "sprint_updated":
        # Sync name / dates if needed
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Sprint).where(Sprint.jira_sprint_id == jira_sprint_id)
            )
            sprint = result.scalar_one_or_none()
            if sprint:
                if sprint_data.get("name"):
                    sprint.name = sprint_data["name"]
                await db.commit()
        logger.info(f"[JiraWebhook] Sprint {jira_sprint_id} updated")


# ─── Comment handler ──────────────────────────────────────────────────────────
async def _handle_comment(payload: dict[str, Any]) -> None:
    issue    = payload.get("issue", {})
    comment  = payload.get("comment", {})
    jira_key = issue.get("key", "")
    body     = comment.get("body", "")

    logger.info(f"[JiraWebhook] Comment on {jira_key}: {body[:60]}")

    # If comment mentions a blocker, flag it
    if any(kw in body.lower() for kw in ["blocked", "blocker", "stuck", "waiting on"]):
        logger.warning(f"[JiraWebhook] Blocker keyword detected in comment on {jira_key}")
        # In full impl: create a RiskAlert or notify boss
