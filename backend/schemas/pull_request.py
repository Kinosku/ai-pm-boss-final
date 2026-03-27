from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from models.pull_request import PRStatus, PRReviewStatus


# ─── Base ────────────────────────────────────────────────────────────────────
class PullRequestBase(BaseModel):
    project_id:       int
    github_pr_number: int
    title:            str         = Field(..., min_length=2, max_length=500)
    description:      Optional[str] = None
    status:           PRStatus    = PRStatus.OPEN
    review_status:    PRReviewStatus = PRReviewStatus.PENDING
    head_branch:      Optional[str] = None
    base_branch:      str           = "main"
    github_url:       Optional[str] = None
    task_id:          Optional[int] = None   # AI-mapped task
    author_id:        Optional[int] = None


# ─── Create (from GitHub webhook) ────────────────────────────────────────────
class PullRequestCreate(PullRequestBase):
    github_pr_id:  Optional[str] = None
    additions:     int = 0
    deletions:     int = 0
    files_changed: int = 0
    opened_at:     Optional[datetime] = None


# ─── Update ──────────────────────────────────────────────────────────────────
class PullRequestUpdate(BaseModel):
    title:          Optional[str]            = None
    description:    Optional[str]            = None
    status:         Optional[PRStatus]       = None
    review_status:  Optional[PRReviewStatus] = None
    task_id:        Optional[int]            = None
    is_stale:       Optional[bool]           = None
    merged_at:      Optional[datetime]       = None
    closed_at:      Optional[datetime]       = None
    additions:      Optional[int]            = None
    deletions:      Optional[int]            = None
    files_changed:  Optional[int]            = None


# ─── Response ────────────────────────────────────────────────────────────────
class PullRequestResponse(PullRequestBase):
    id:            int
    github_pr_id:  Optional[str] = None
    additions:     int
    deletions:     int
    files_changed: int
    is_stale:      bool
    opened_at:     Optional[datetime] = None
    merged_at:     Optional[datetime] = None
    closed_at:     Optional[datetime] = None
    created_at:    datetime
    updated_at:    Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Summary (for employee My PRs page) ──────────────────────────────────────
class PullRequestSummary(BaseModel):
    id:               int
    github_pr_number: int
    title:            str
    status:           PRStatus
    review_status:    PRReviewStatus
    head_branch:      Optional[str] = None
    is_stale:         bool
    opened_at:        Optional[datetime] = None
    github_url:       Optional[str] = None

    model_config = {"from_attributes": True}
