from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from models.integration import IntegrationProvider, IntegrationStatus


# ─── Base ────────────────────────────────────────────────────────────────────
class IntegrationBase(BaseModel):
    project_id: int
    provider:   IntegrationProvider
    status:     IntegrationStatus = IntegrationStatus.DISCONNECTED
    config:     dict              = {}


# ─── Create ──────────────────────────────────────────────────────────────────
class IntegrationCreate(IntegrationBase):
    access_token:   Optional[str] = None
    refresh_token:  Optional[str] = None
    webhook_secret: Optional[str] = None


# ─── Update ──────────────────────────────────────────────────────────────────
class IntegrationUpdate(BaseModel):
    status:          Optional[IntegrationStatus] = None
    config:          Optional[dict]              = None
    access_token:    Optional[str]               = None
    refresh_token:   Optional[str]               = None
    webhook_secret:  Optional[str]               = None
    is_webhook_live: Optional[bool]              = None
    sync_error:      Optional[str]               = None
    last_synced_at:  Optional[datetime]          = None


# ─── Response (no tokens exposed) ────────────────────────────────────────────
class IntegrationResponse(IntegrationBase):
    id:              int
    is_webhook_live: bool
    last_synced_at:  Optional[datetime] = None
    sync_error:      Optional[str]      = None
    token_expires:   Optional[datetime] = None
    created_at:      datetime
    updated_at:      Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Connect request (for integrations page "Connect" button) ─────────────────
class IntegrationConnectRequest(BaseModel):
    project_id:    int
    provider:      IntegrationProvider

    # GitHub
    github_repo:          Optional[str] = None   # "org/repo-name"
    github_token:         Optional[str] = None

    # Slack
    slack_bot_token:      Optional[str] = None
    slack_channel_id:     Optional[str] = None

    # Jira
    jira_base_url:        Optional[str] = None
    jira_email:           Optional[str] = None
    jira_api_token:       Optional[str] = None
    jira_project_key:     Optional[str] = None


# ─── Sync status response ─────────────────────────────────────────────────────
class IntegrationSyncResponse(BaseModel):
    provider:       IntegrationProvider
    status:         IntegrationStatus
    last_synced_at: Optional[datetime] = None
    sync_error:     Optional[str]      = None
    is_webhook_live:bool               = False
    message:        str                = ""
