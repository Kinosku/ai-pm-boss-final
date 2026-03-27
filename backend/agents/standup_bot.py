"""
Standup Bot Agent
Collects async standup updates from developers via Slack,
synthesises them with LLM, posts the summary to the team channel.
"""
import logging
from typing import Any
from datetime import datetime, date

from sqlalchemy import select

from database import AsyncSessionLocal
from models.standup import Standup, StandupStatus
from models.developer import Developer
from models.integration import Integration, IntegrationProvider, IntegrationStatus
from ai.llm import invoke_llm_json, load_prompt
from ai.memory import AgentName, save_memory, append_to_history
from core.queue import enqueue_notification

logger = logging.getLogger(__name__)


class StandupBotAgent:
    """
    Agent that:
    1. Fetches today's individual standup updates from DB
    2. Identifies which developers haven't submitted
    3. Sends reminders to missing devs via Slack DM
    4. Calls LLM to synthesise a team summary
    5. Posts summary to the team Slack channel
    6. Persists summary Standup row in DB
    """

    name    = AgentName.STANDUP_BOT
    display = "Standup Bot"

    async def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_id = payload.get("project_id")
        channel_id = payload.get("channel_id", "")
        sprint_id  = payload.get("sprint_id")

        logger.info(f"[StandupBotAgent] Running for project={project_id} channel={channel_id}")

        async with AsyncSessionLocal() as db:
            today_start = datetime.combine(date.today(), datetime.min.time())

            # 1. Fetch today's updates
            updates_result = await db.execute(
                select(Standup).where(
                    Standup.project_id   == project_id,
                    Standup.standup_date >= today_start,
                    Standup.is_summary   == False,
                )
            )
            updates = updates_result.scalars().all()

            # 2. Identify all team developers
            devs_result = await db.execute(
                select(Developer).where(Developer.project_id == project_id)
            )
            all_devs = devs_result.scalars().all()

            submitted_dev_ids  = {u.developer_id for u in updates if u.developer_id}
            missing_devs       = [d for d in all_devs if d.id not in submitted_dev_ids]

            # 3. Send Slack DM reminders to missing devs
            slack_intg = await self._get_slack_integration(db, project_id)
            if slack_intg and missing_devs:
                await self._send_reminders(slack_intg, missing_devs)

            # 4. Build prompt context
            dev_updates_text = self._format_updates(updates)

            if not updates:
                logger.info("[StandupBotAgent] No updates collected yet — skipping summary.")
                return {"status": "no_updates", "project_id": project_id}

            # 5. Get sprint info
            sprint_info = await self._get_sprint_info(db, sprint_id, project_id)

            # 6. Call LLM for summary
            system_prompt = load_prompt("standup_prompt.txt").format(
                project_name        = f"Project {project_id}",
                standup_date        = str(date.today()),
                sprint_name         = sprint_info.get("name", "Current Sprint"),
                sprint_day          = sprint_info.get("day", "N/A"),
                sprint_total_days   = sprint_info.get("total_days", "N/A"),
                sprint_health_score = sprint_info.get("health_score", "N/A"),
                developer_updates   = dev_updates_text,
            )

            try:
                summary_data = await invoke_llm_json(system_prompt, "Generate the standup summary.")
            except Exception as e:
                logger.error(f"[StandupBotAgent] LLM error: {e}")
                summary_data = self._fallback_summary(updates, missing_devs)

            summary_text  = summary_data.get("summary_text", "")
            blockers      = summary_data.get("blockers", [])
            missing_names = summary_data.get("developers_missing", [])

            # 7. Post to Slack
            slack_ts = None
            if slack_intg and channel_id and summary_text:
                slack_ts = await self._post_to_slack(slack_intg, channel_id, summary_text)

            # 8. Persist summary row
            summary_row = Standup(
                project_id    = project_id,
                sprint_id     = sprint_id,
                standup_date  = datetime.utcnow(),
                is_summary    = True,
                summary_text  = summary_text,
                blockers_json = blockers,
                slack_channel = channel_id,
                slack_message_ts = slack_ts,
                status        = StandupStatus.POSTED if slack_ts else StandupStatus.COLLECTED,
            )
            db.add(summary_row)

            # 9. Notify boss if there are blockers
            if blockers:
                high_blockers = [b for b in blockers if b.get("severity") == "high"]
                if high_blockers:
                    await enqueue_notification(
                        user_id    = project_id,
                        message    = f"🚨 {len(high_blockers)} blocker(s) reported in today's standup",
                        notif_type = "blocker",
                    )

            await db.commit()

        # 10. Persist memory
        await save_memory(project_id, self.name, {
            "last_run_date":        str(date.today()),
            "updates_collected":    len(updates),
            "missing_devs":         len(missing_devs),
            "blockers_found":       len(blockers),
            "slack_posted":         bool(slack_ts),
        })
        await append_to_history(project_id, self.name, {
            "action":     "standup_summary_posted",
            "date":       str(date.today()),
            "updates":    len(updates),
            "blockers":   len(blockers),
            "missing":    len(missing_devs),
        })

        logger.info(
            f"[StandupBotAgent] Summary posted | Updates={len(updates)} | "
            f"Blockers={len(blockers)} | Missing={len(missing_devs)}"
        )
        return {
            "status":            "success",
            "updates_collected": len(updates),
            "blockers_found":    len(blockers),
            "missing_devs":      len(missing_devs),
            "slack_posted":      bool(slack_ts),
            "overall_sentiment": summary_data.get("overall_sentiment", "neutral"),
        }

    # ─── Format updates for LLM ───────────────────────────────────────────────
    @staticmethod
    def _format_updates(updates: list[Standup]) -> str:
        if not updates:
            return "No updates submitted yet."
        lines = []
        for u in updates:
            lines.append(
                f"Developer ID {u.developer_id}:\n"
                f"  Done:    {', '.join(u.done)    or 'N/A'}\n"
                f"  Doing:   {', '.join(u.doing)   or 'N/A'}\n"
                f"  Blocked: {', '.join(u.blocked) or 'None'}"
            )
        return "\n\n".join(lines)

    # ─── Slack helpers ────────────────────────────────────────────────────────
    @staticmethod
    async def _get_slack_integration(db, project_id: int) -> Integration | None:
        result = await db.execute(
            select(Integration).where(
                Integration.project_id == project_id,
                Integration.provider   == IntegrationProvider.SLACK,
                Integration.status     == IntegrationStatus.CONNECTED,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _send_reminders(integration: Integration, missing_devs: list[Developer]) -> None:
        if not integration.access_token:
            return
        try:
            from slack_sdk.web.async_client import AsyncWebClient
            client = AsyncWebClient(token=integration.access_token)
            for dev in missing_devs:
                if dev.slack_user_id:
                    await client.chat_postMessage(
                        channel = dev.slack_user_id,
                        text    = "👋 Reminder: Please submit your standup update! Reply with:\n*Done:* ...\n*Doing:* ...\n*Blocked:* ...",
                    )
        except Exception as e:
            logger.warning(f"[StandupBotAgent] Reminder send failed: {e}")

    @staticmethod
    async def _post_to_slack(integration: Integration, channel_id: str, message: str) -> str | None:
        if not integration.access_token:
            return None
        try:
            from slack_sdk.web.async_client import AsyncWebClient
            client   = AsyncWebClient(token=integration.access_token)
            response = await client.chat_postMessage(channel=channel_id, text=message)
            return response.get("ts")
        except Exception as e:
            logger.error(f"[StandupBotAgent] Slack post failed: {e}")
            return None

    # ─── Sprint info ──────────────────────────────────────────────────────────
    @staticmethod
    async def _get_sprint_info(db, sprint_id: int | None, project_id: int) -> dict:
        from models.sprint import Sprint, SprintStatus
        if sprint_id:
            result = await db.execute(select(Sprint).where(Sprint.id == sprint_id))
        else:
            result = await db.execute(
                select(Sprint).where(
                    Sprint.project_id == project_id,
                    Sprint.status     == SprintStatus.ACTIVE,
                ).limit(1)
            )
        sprint = result.scalar_one_or_none()
        if not sprint:
            return {"name": "Current Sprint", "day": "N/A", "total_days": "N/A", "health_score": "N/A"}

        today      = date.today()
        start      = sprint.start_date.date() if sprint.start_date else today
        end        = sprint.end_date.date()   if sprint.end_date   else today
        total_days = max((end - start).days, 1)
        sprint_day = min((today - start).days + 1, total_days)

        return {
            "name":         sprint.name,
            "day":          sprint_day,
            "total_days":   total_days,
            "health_score": sprint.health_score or "N/A",
        }

    # ─── Fallback summary ─────────────────────────────────────────────────────
    @staticmethod
    def _fallback_summary(updates: list[Standup], missing_devs: list[Developer]) -> dict:
        lines = [f"📋 Daily Standup — {date.today()}\n"]
        for u in updates:
            if u.done:   lines.append(f"✅ Dev {u.developer_id}: {', '.join(u.done)}")
            if u.blocked:lines.append(f"🚨 Blocked: {', '.join(u.blocked)}")
        if missing_devs:
            lines.append(f"\n⚠️ No update from: Dev {', '.join(str(d.id) for d in missing_devs)}")
        return {
            "summary_text":        "\n".join(lines),
            "blockers":            [],
            "developers_reported": [str(u.developer_id) for u in updates],
            "developers_missing":  [str(d.id) for d in missing_devs],
            "overall_sentiment":   "neutral",
        }


# ─── Singleton ───────────────────────────────────────────────────────────────
standup_bot_agent = StandupBotAgent()
