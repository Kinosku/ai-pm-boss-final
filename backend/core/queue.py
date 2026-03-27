from enum import Enum
from typing import Any
import json

from core.redis import get_redis


# ─── Queue Names ─────────────────────────────────────────────────────────────
class QueueName(str, Enum):
    TASK_CREATION   = "queue:task_creation"
    PR_MAPPING      = "queue:pr_mapping"
    RISK_DETECTION  = "queue:risk_detection"
    REPORT_GEN      = "queue:report_generation"
    STANDUP_BOT     = "queue:standup_bot"
    NOTIFICATIONS   = "queue:notifications"


# ─── Priority Levels ─────────────────────────────────────────────────────────
class Priority(int, Enum):
    LOW    = 1
    MEDIUM = 5
    HIGH   = 10


# ─── Enqueue ─────────────────────────────────────────────────────────────────
async def enqueue(
    queue: QueueName,
    payload: dict[str, Any],
    priority: Priority = Priority.MEDIUM,
) -> None:
    """
    Push a job onto the specified Redis list queue.
    Payload is stored as JSON alongside its priority.
    """
    client = await get_redis()
    message = json.dumps({"priority": priority, "data": payload})
    await client.lpush(queue.value, message)


# ─── Dequeue ─────────────────────────────────────────────────────────────────
async def dequeue(queue: QueueName, timeout: int = 5) -> dict[str, Any] | None:
    """
    Blocking pop from the queue (used by workers).
    Returns the parsed payload dict or None on timeout.
    """
    client = await get_redis()
    result = await client.brpop(queue.value, timeout=timeout)
    if result is None:
        return None
    _, raw = result
    return json.loads(raw)


# ─── Queue Length ────────────────────────────────────────────────────────────
async def queue_length(queue: QueueName) -> int:
    """Return the number of pending jobs in a queue."""
    client = await get_redis()
    return await client.llen(queue.value)


# ─── Convenience helpers ─────────────────────────────────────────────────────

async def enqueue_task_creation(project_id: int, prd_text: str) -> None:
    await enqueue(
        QueueName.TASK_CREATION,
        {"project_id": project_id, "prd_text": prd_text},
        Priority.HIGH,
    )


async def enqueue_pr_mapping(pr_id: int, project_id: int) -> None:
    await enqueue(
        QueueName.PR_MAPPING,
        {"pr_id": pr_id, "project_id": project_id},
        Priority.MEDIUM,
    )


async def enqueue_risk_detection(project_id: int, sprint_id: int) -> None:
    await enqueue(
        QueueName.RISK_DETECTION,
        {"project_id": project_id, "sprint_id": sprint_id},
        Priority.HIGH,
    )


async def enqueue_report_generation(project_id: int, report_type: str) -> None:
    await enqueue(
        QueueName.REPORT_GEN,
        {"project_id": project_id, "report_type": report_type},
        Priority.LOW,
    )


async def enqueue_standup(project_id: int, channel_id: str) -> None:
    await enqueue(
        QueueName.STANDUP_BOT,
        {"project_id": project_id, "channel_id": channel_id},
        Priority.MEDIUM,
    )


async def enqueue_notification(user_id: int, message: str, notif_type: str) -> None:
    await enqueue(
        QueueName.NOTIFICATIONS,
        {"user_id": user_id, "message": message, "type": notif_type},
        Priority.MEDIUM,
    )
