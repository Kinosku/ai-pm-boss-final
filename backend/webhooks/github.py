"""
GitHub Webhook Handler
Receives GitHub events (PR opened/merged, push, etc.)
→ verifies HMAC signature → routes to orchestrator.
"""
import hashlib
import hmac
import logging
from typing import Any

from fastapi import APIRouter, Request, HTTPException, Header
from sqlalchemy import select

from core.config import settings
from database import AsyncSessionLocal
from models.integration import Integration, IntegrationProvider, IntegrationStatus
from models.pull_request import PullRequest, PRStatus
from models.developer import Developer
from ai.orchestrator import orchestrator, OrchestratorEvent

router = APIRouter()
logger = logging.getLogger(__name__)


# ─── Signature verification ───────────────────────────────────────────────────
def _verify_github_signature(payload: bytes, signature: str) -> bool:
    """Verify the X-Hub-Signature-256 header from GitHub."""
    if not settings.GITHUB_WEBHOOK_SECRET:
        return True  # Skip in dev if secret not set
    expected = "sha256=" + hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature or "")


# ─── Project resolver ─────────────────────────────────────────────────────────
async def _resolve_project(repo_full_name: str) -> int | None:
    """Find project_id from GitHub repo name (e.g. 'org/repo')."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Integration).where(
                Integration.provider == IntegrationProvider.GITHUB,
                Integration.status   == IntegrationStatus.CONNECTED,
            )
        )
        integrations = result.scalars().all()
        for intg in integrations:
            if intg.config.get("repo") == repo_full_name:
                return intg.project_id
    return None


async def _resolve_author(github_username: str) -> int | None:
    """Find developer_id from GitHub username."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Developer).where(Developer.github_username == github_username)
        )
        dev = result.scalar_one_or_none()
        return dev.id if dev else None


# ─── Main webhook endpoint ────────────────────────────────────────────────────
@router.post("/")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    x_github_event:      str = Header(None),
):
    body = await request.body()

    # Verify signature
    if not _verify_github_signature(body, x_hub_signature_256 or ""):
        raise HTTPException(status_code=401, detail="Invalid GitHub webhook signature")

    payload: dict[str, Any] = await request.json()
    event = x_github_event or "unknown"

    logger.info(f"[GitHubWebhook] Event={event}")

    # ── Pull Request events ──────────────────────────────────────────────────
    if event == "pull_request":
        await _handle_pull_request(payload)

    # ── Push / commit events ─────────────────────────────────────────────────
    elif event == "push":
        await _handle_push(payload)

    # ── PR review events ─────────────────────────────────────────────────────
    elif event == "pull_request_review":
        await _handle_pr_review(payload)

    else:
        logger.debug(f"[GitHubWebhook] Unhandled event: {event}")

    return {"status": "received", "event": event}


# ─── PR handler ───────────────────────────────────────────────────────────────
async def _handle_pull_request(payload: dict[str, Any]) -> None:
    action      = payload.get("action")
    pr_data     = payload.get("pull_request", {})
    repo        = payload.get("repository", {})
    repo_name   = repo.get("full_name", "")
    sender      = payload.get("sender", {})

    project_id = await _resolve_project(repo_name)
    if not project_id:
        logger.warning(f"[GitHubWebhook] No project mapped to repo: {repo_name}")
        return

    author_id = await _resolve_author(sender.get("login", ""))

    async with AsyncSessionLocal() as db:
        pr_number = pr_data.get("number")

        if action == "opened":
            # Persist PR
            pr = PullRequest(
                project_id       = project_id,
                github_pr_number = pr_number,
                github_pr_id     = str(pr_data.get("id", "")),
                title            = pr_data.get("title", ""),
                description      = pr_data.get("body", ""),
                status           = PRStatus.OPEN,
                head_branch      = pr_data.get("head", {}).get("ref"),
                base_branch      = pr_data.get("base", {}).get("ref", "main"),
                github_url       = pr_data.get("html_url"),
                author_id        = author_id,
                additions        = pr_data.get("additions", 0),
                deletions        = pr_data.get("deletions", 0),
                files_changed    = pr_data.get("changed_files", 0),
            )
            db.add(pr)
            await db.commit()
            await db.refresh(pr)

            # Trigger PR mapper agent
            await orchestrator.handle_event(
                OrchestratorEvent.GITHUB_PR_OPENED,
                project_id,
                {"pr_id": pr.id},
            )
            logger.info(f"[GitHubWebhook] PR #{pr_number} opened → mapper queued")

        elif action == "closed":
            result = await db.execute(
                select(PullRequest).where(
                    PullRequest.github_pr_number == pr_number,
                    PullRequest.project_id       == project_id,
                )
            )
            pr = result.scalar_one_or_none()
            if pr:
                from datetime import datetime
                is_merged = pr_data.get("merged", False)
                pr.status    = PRStatus.MERGED if is_merged else PRStatus.CLOSED
                pr.merged_at = datetime.utcnow() if is_merged else None
                pr.closed_at = datetime.utcnow()
                await db.commit()

                if is_merged:
                    await orchestrator.handle_event(
                        OrchestratorEvent.GITHUB_PR_MERGED,
                        project_id,
                        {"pr_id": pr.id},
                    )
                logger.info(f"[GitHubWebhook] PR #{pr_number} {'merged' if is_merged else 'closed'}")

        elif action in ("review_requested", "ready_for_review"):
            logger.info(f"[GitHubWebhook] PR #{pr_number} action={action}")


# ─── Push handler ─────────────────────────────────────────────────────────────
async def _handle_push(payload: dict[str, Any]) -> None:
    repo      = payload.get("repository", {})
    repo_name = repo.get("full_name", "")
    sender    = payload.get("sender", {})
    commits   = payload.get("commits", [])

    project_id = await _resolve_project(repo_name)
    if not project_id:
        return

    # Update developer last_commit_at
    author_id = await _resolve_author(sender.get("login", ""))
    if author_id:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Developer).where(Developer.id == author_id))
            dev = result.scalar_one_or_none()
            if dev:
                from datetime import datetime
                dev.last_commit_at = datetime.utcnow()
                await db.commit()

    # Trigger risk detection on each push
    if commits:
        await orchestrator.handle_event(
            OrchestratorEvent.GITHUB_COMMIT,
            project_id,
            {"commit_count": len(commits), "sprint_id": None},
        )

    logger.info(f"[GitHubWebhook] Push: {len(commits)} commits to {repo_name}")


# ─── PR review handler ────────────────────────────────────────────────────────
async def _handle_pr_review(payload: dict[str, Any]) -> None:
    action  = payload.get("action")
    review  = payload.get("review", {})
    pr_data = payload.get("pull_request", {})
    repo    = payload.get("repository", {})

    if action != "submitted":
        return

    project_id = await _resolve_project(repo.get("full_name", ""))
    if not project_id:
        return

    review_state = review.get("state", "")     # "approved" | "changes_requested"
    pr_number    = pr_data.get("number")

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(PullRequest).where(
                PullRequest.github_pr_number == pr_number,
                PullRequest.project_id       == project_id,
            )
        )
        pr = result.scalar_one_or_none()
        if pr:
            from models.pull_request import PRReviewStatus
            if review_state == "approved":
                pr.review_status = PRReviewStatus.APPROVED
            elif review_state == "changes_requested":
                pr.review_status = PRReviewStatus.CHANGES_REQUESTED
            await db.commit()

    logger.info(f"[GitHubWebhook] PR #{pr_number} review={review_state}")
