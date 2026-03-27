import redis.asyncio as aioredis
from redis.asyncio import Redis
from typing import Optional
import json

from core.config import settings

# ─── Global client instance ──────────────────────────────────────────────────
_redis_client: Optional[Redis] = None


async def get_redis() -> Redis:
    """Return (and lazily create) the shared async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis():
    """Close the Redis connection — call on app shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


# ─── Helpers ─────────────────────────────────────────────────────────────────

async def redis_set(key: str, value: dict | str, ttl: int = 3600) -> None:
    """Store a value in Redis. Dicts are JSON-serialised automatically."""
    client = await get_redis()
    payload = json.dumps(value) if isinstance(value, dict) else value
    await client.setex(key, ttl, payload)


async def redis_get(key: str) -> dict | str | None:
    """Retrieve a value from Redis. JSON strings are deserialised automatically."""
    client = await get_redis()
    raw = await client.get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw


async def redis_delete(key: str) -> None:
    """Delete a key from Redis."""
    client = await get_redis()
    await client.delete(key)


async def redis_exists(key: str) -> bool:
    """Check whether a key exists in Redis."""
    client = await get_redis()
    return bool(await client.exists(key))


async def redis_publish(channel: str, message: dict) -> None:
    """Publish a message to a Redis pub/sub channel."""
    client = await get_redis()
    await client.publish(channel, json.dumps(message))
