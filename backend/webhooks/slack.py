"""
Slack Webhook / Event Handler
Handles Slack Events API, slash commands, and interactive payloads.
Verifies request signature → routes messages to SlackParser / Orchestrator.
"""
import hashlib
import hmac
import time
import json
import logging
from typing import Any

from fastapi import APIRouter, Request, HTTPException, Form
from sqlalchemy import select

from core.config import settings
from database import AsyncSessionLocal
from models.integration import Integration, IntegrationProvider, IntegrationStatus
from models.developer import Developer
from services.slack_parser import slack_parser
from ai.orchestrator import orchestrator, OrchestratorEvent

router = APIRouter()
logger = logging.getLogger(__name__)


# ─── Signature verification ───────────────────────────────────────────────────
def _verify_slack_signature(body: bytes, timestamp: str, signature: str) -> bool:
    """Verify Slack's X-Slack-Signature header."""
    if not settings.SLACK_SIGNING_SECRET:
        return True
    if abs(time.time() - float(timestamp)) > 300:
        return False   # Replay attack guard (5 min window)
    base_string = f"v0:{timestamp}:{body.decode()}"
    expected    = "v0=" + hmac.new(
        settings.SLACK_SIGNING_SECRET.encode(),
        base_string.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ─── Project resolver ─────────────────────────────────────────────────────────
async def _resolve_project_from_channel(channel_id: str) -> int | None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Integration).where(
                Integration.provider == IntegrationProvider.SLACK,
                Integration.status   == IntegrationStatus.CONNECTED,
            )
        )
        integrations = result.scalars().all()
        for intg in integrations:
            if intg.config.get("channel_id") == channel_id:
                return intg.project_id
    return None


async def _resolve_developer(slack_user_id: str) -> Developer | None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Developer).where(Developer.slack_user_id == slack_user_id)
        )
        return result.scalar_one_or_none()


# ─── Main Events API endpoint ────────────────────────────────────────────────
@router.post("/events")
async def slack_events(request: Request):
    body = await request.body()

    # Verify signature
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")
    if not _verify_slack_signature(body, timestamp, signature):
        raise HTTPException(status_code=401, detail="Invalid Slack signature")

    payload: dict[str, Any] = await request.json()
    event_type = payload.get("type")

    # ── URL verification challenge (Slack setup) ─────────────────────────────
    if event_type == "url_verification":
        return {"challenge": payload.get("challenge")}

    # ── Event callback ───────────────────────────────────────────────────────
    if event_type == "event_callback":
        event = payload.get("event", {})
        await _route_event(event, payload)

    return {"status": "ok"}


# ─── Slash commands endpoint ──────────────────────────────────────────────────
@router.post("/commands")
async def slack_commands(
    request:     Request,
    command:     str = Form(...),
    text:        str = Form(""),
    user_id:     str = Form(""),
    channel_id:  str = Form(""),
    response_url:str = Form(""),
):
    body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")
    if not _verify_slack_signature(body, timestamp, signature):
        raise HTTPException(status_code=401, detail="Invalid Slack signature")

    logger.info(f"[SlackWebhook] Command={command} User={user_id} Channel={channel_id}")

    project_id = await _resolve_project_from_channel(channel_id)

    # ── /standup ─────────────────────────────────────────────────────────────
    if command == "/standup":
        dev = await _resolve_developer(user_id)
        if dev and project_id:
            parsed = slack_parser._parse_standup_message(text, user_id)
            # Queue standup update
            from core.queue import enqueue
            from core.queue import QueueName
            await enqueue(QueueName.STANDUP_BOT, {
                "project_id":   project_id,
                "developer_id": dev.id,
                "done":         parsed.get("done", []),
                "doing":        parsed.get("doing", []),
                "blocked":      parsed.get("blocked", []),
                "raw_message":  text,
                "channel_id":   channel_id,
            })
            return {"response_type": "ephemeral", "text": "✅ Standup update received! Thanks."}
        return {"response_type": "ephemeral", "text": "⚠️ Developer profile not found. Please set up your profile first."}

    # ── /task ─────────────────────────────────────────────────────────────────
    elif command == "/task":
        if project_id and text.strip():
            await orchestrator.handle_event(
                OrchestratorEvent.SLACK_MESSAGE,
                project_id,
                {"text": text, "user": user_id, "channel": channel_id, "ts": ""},
            )
            return {"response_type": "ephemeral", "text": "🤖 AI PM Boss is creating tasks from your message..."}
        return {"response_type": "ephemeral", "text": "⚠️ Please provide a task description."}

    # ── /report ───────────────────────────────────────────────────────────────
    elif command == "/report":
        if project_id:
            await orchestrator.handle_event(
                OrchestratorEvent.WEEKLY_REPORT_TIME,
                project_id,
                {"report_type": text.strip() or "weekly"},
            )
            return {"response_type": "ephemeral", "text": "📊 Generating report... It will be posted here shortly."}

    return {"response_type": "ephemeral", "text": f"Unknown command: {command}"}


# ─── Interactive payloads (buttons, modals) ───────────────────────────────────
@router.post("/interactive")
async def slack_interactive(request: Request, payload: str = Form(...)):
    body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")
    if not _verify_slack_signature(body, timestamp, signature):
        raise HTTPException(status_code=401, detail="Invalid Slack signature")

    data: dict[str, Any] = json.loads(payload)
    action_type = data.get("type")
    user_id     = data.get("user", {}).get("id", "")
    channel_id  = data.get("channel", {}).get("id", "")

    logger.info(f"[SlackWebhook] Interactive type={action_type} user={user_id}")

    if action_type == "block_actions":
        actions = data.get("actions", [])
        for action in actions:
            action_id = action.get("action_id", "")

            if action_id == "resolve_blocker":
                # Boss clicked "Resolve Blocker" in a notification
                alert_id = action.get("value")
                logger.info(f"[SlackWebhook] Boss resolved blocker alert_id={alert_id}")

            elif action_id == "view_report":
                logger.info("[SlackWebhook] Boss clicked 'View Report'")

    return {"status": "ok"}


# ─── Event router ─────────────────────────────────────────────────────────────
async def _route_event(event: dict[str, Any], payload: dict) -> None:
    event_type = event.get("type", "")
    user_id    = event.get("user", "")
    channel    = event.get("channel", "")
    text       = event.get("text", "")
    bot_id     = event.get("bot_id")

    # Ignore bot messages to avoid loops
    if bot_id:
        return

    project_id = await _resolve_project_from_channel(channel)
    if not project_id:
        logger.debug(f"[SlackWebhook] No project for channel {channel}")
        return

    # ── Message events ───────────────────────────────────────────────────────
    if event_type in ("message", "app_mention"):
        result = await slack_parser.handle_message(
            event      = {"text": text, "user": user_id, "channel": channel, "ts": event.get("ts", "")},
            project_id = project_id,
        )
        logger.info(f"[SlackWebhook] Message intent={result.get('intent')} action={result.get('action')}")

        # If tasks were extracted, trigger task creation
        if result.get("action") == "tasks_extracted":
            await orchestrator.handle_event(
                OrchestratorEvent.SLACK_MESSAGE,
                project_id,
                {"text": text, "user": user_id, "channel": channel, "ts": event.get("ts", "")},
            )

    # ── Member joined channel ────────────────────────────────────────────────
    elif event_type == "member_joined_channel":
        logger.info(f"[SlackWebhook] Member {user_id} joined channel {channel}")
