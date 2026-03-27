"""
AI Memory — per-project, per-agent short-term memory backed by Redis.
Each agent gets its own key namespace so contexts don't bleed across agents.
"""
import json
from typing import Any, Optional

from core.redis import get_redis

# TTL for agent memory in seconds (default: 24 hours)
MEMORY_TTL = 60 * 60 * 24


def _memory_key(project_id: int, agent_name: str) -> str:
    return f"memory:{agent_name}:project:{project_id}"


# ─── Save / Load ─────────────────────────────────────────────────────────────

async def save_memory(project_id: int, agent_name: str, data: dict[str, Any]) -> None:
    """Persist agent memory for a project."""
    client = await get_redis()
    key = _memory_key(project_id, agent_name)
    await client.setex(key, MEMORY_TTL, json.dumps(data))


async def load_memory(project_id: int, agent_name: str) -> Optional[dict[str, Any]]:
    """Load agent memory for a project. Returns None if no memory exists."""
    client = await get_redis()
    key = _memory_key(project_id, agent_name)
    raw = await client.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def clear_memory(project_id: int, agent_name: str) -> None:
    """Clear agent memory for a project."""
    client = await get_redis()
    key = _memory_key(project_id, agent_name)
    await client.delete(key)


# ─── Append to history list ──────────────────────────────────────────────────

async def append_to_history(
    project_id: int,
    agent_name: str,
    entry: dict[str, Any],
    max_entries: int = 20,
) -> None:
    """
    Append an event/action entry to the agent's history list.
    Automatically trims to max_entries to avoid unbounded growth.
    """
    client = await get_redis()
    key = f"history:{agent_name}:project:{project_id}"
    await client.lpush(key, json.dumps(entry))
    await client.ltrim(key, 0, max_entries - 1)
    await client.expire(key, MEMORY_TTL)


async def get_history(
    project_id: int,
    agent_name: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Retrieve the last N history entries for an agent."""
    client = await get_redis()
    key = f"history:{agent_name}:project:{project_id}"
    raw_list = await client.lrange(key, 0, limit - 1)
    return [json.loads(item) for item in raw_list]


# ─── Named Agent Constants ───────────────────────────────────────────────────
class AgentName:
    TASK_CREATOR    = "task_creator"
    PR_MAPPER       = "pr_mapper"
    DELAY_PREDICTOR = "delay_predictor"
    REPORT_GENERATOR = "report_generator"
    STANDUP_BOT     = "standup_bot"
