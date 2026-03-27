from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from database import get_db
from models.integration import Integration, IntegrationProvider, IntegrationStatus
from models.user import User
from schemas.integration import (
    IntegrationCreate, IntegrationUpdate,
    IntegrationResponse, IntegrationConnectRequest,
    IntegrationSyncResponse,
)
from routers.auth import get_current_user, require_boss

router = APIRouter()


@router.get("/", response_model=List[IntegrationResponse])
async def list_integrations(
    project_id: int        = Query(...),
    db: AsyncSession        = Depends(get_db),
    current_user: User      = Depends(get_current_user),
):
    result = await db.execute(
        select(Integration).where(Integration.project_id == project_id)
    )
    return result.scalars().all()


@router.post("/connect", response_model=IntegrationResponse)
async def connect_integration(
    payload: IntegrationConnectRequest,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(require_boss),
):
    """Connect button on the Integrations page."""
    # Check if already exists
    result = await db.execute(
        select(Integration).where(
            Integration.project_id == payload.project_id,
            Integration.provider   == payload.provider,
        )
    )
    existing = result.scalar_one_or_none()

    # Build provider-specific config
    config = {}
    access_token   = None
    webhook_secret = None

    if payload.provider == IntegrationProvider.GITHUB:
        config       = {"repo": payload.github_repo}
        access_token = payload.github_token

    elif payload.provider == IntegrationProvider.SLACK:
        config       = {"channel_id": payload.slack_channel_id}
        access_token = payload.slack_bot_token

    elif payload.provider == IntegrationProvider.JIRA:
        config = {
            "project_key": payload.jira_project_key,
            "base_url":    payload.jira_base_url,
            "email":       payload.jira_email,
        }
        access_token = payload.jira_api_token

    if existing:
        existing.status        = IntegrationStatus.CONNECTED
        existing.config        = config
        existing.access_token  = access_token
        existing.last_synced_at= datetime.utcnow()
        await db.flush()
        await db.refresh(existing)
        return existing

    integration = Integration(
        project_id     = payload.project_id,
        provider       = payload.provider,
        status         = IntegrationStatus.CONNECTED,
        config         = config,
        access_token   = access_token,
        webhook_secret = webhook_secret,
        last_synced_at = datetime.utcnow(),
    )
    db.add(integration)
    await db.flush()
    await db.refresh(integration)
    return integration


@router.post("/{integration_id}/disconnect", response_model=IntegrationResponse)
async def disconnect_integration(
    integration_id: int,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(require_boss),
):
    intg = await _get_or_404(db, integration_id)
    intg.status        = IntegrationStatus.DISCONNECTED
    intg.access_token  = None
    intg.refresh_token = None
    await db.flush()
    await db.refresh(intg)
    return intg


@router.post("/{integration_id}/sync", response_model=IntegrationSyncResponse)
async def sync_integration(
    integration_id: int,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(require_boss),
):
    """Trigger a manual sync for an integration."""
    intg = await _get_or_404(db, integration_id)

    try:
        intg.last_synced_at = datetime.utcnow()
        intg.sync_error     = None
        await db.flush()
        message = f"{intg.provider} synced successfully"
    except Exception as e:
        intg.sync_error = str(e)
        intg.status     = IntegrationStatus.ERROR
        await db.flush()
        message = f"Sync failed: {str(e)}"

    return IntegrationSyncResponse(
        provider        = intg.provider,
        status          = intg.status,
        last_synced_at  = intg.last_synced_at,
        sync_error      = intg.sync_error,
        is_webhook_live = intg.is_webhook_live,
        message         = message,
    )


@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: int,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _get_or_404(db, integration_id)


# ─── Helper ──────────────────────────────────────────────────────────────────
async def _get_or_404(db: AsyncSession, integration_id: int) -> Integration:
    result = await db.execute(select(Integration).where(Integration.id == integration_id))
    intg   = result.scalar_one_or_none()
    if not intg:
        raise HTTPException(status_code=404, detail="Integration not found")
    return intg
