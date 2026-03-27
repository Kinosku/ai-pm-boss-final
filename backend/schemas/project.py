from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from models.project import ProjectStatus


# ─── Base ────────────────────────────────────────────────────────────────────
class ProjectBase(BaseModel):
    name:          str            = Field(..., min_length=2, max_length=255)
    description:   Optional[str] = None
    status:        ProjectStatus  = ProjectStatus.ACTIVE
    github_repo:   Optional[str] = None
    jira_project:  Optional[str] = None
    slack_channel: Optional[str] = None


# ─── Create ──────────────────────────────────────────────────────────────────
class ProjectCreate(ProjectBase):
    pass


# ─── Update ──────────────────────────────────────────────────────────────────
class ProjectUpdate(BaseModel):
    name:          Optional[str]           = None
    description:   Optional[str]           = None
    status:        Optional[ProjectStatus] = None
    github_repo:   Optional[str]           = None
    jira_project:  Optional[str]           = None
    slack_channel: Optional[str]           = None
    is_active:     Optional[bool]          = None


# ─── Response ────────────────────────────────────────────────────────────────
class ProjectResponse(ProjectBase):
    id:         int
    owner_id:   int
    is_active:  bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Summary (for lists/dashboard) ───────────────────────────────────────────
class ProjectSummary(BaseModel):
    id:     int
    name:   str
    status: ProjectStatus

    model_config = {"from_attributes": True}
