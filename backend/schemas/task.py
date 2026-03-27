from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from models.task import TaskStatus, TaskPriority, TaskSource


# ─── Base ────────────────────────────────────────────────────────────────────
class TaskBase(BaseModel):
    title:        str          = Field(..., min_length=2, max_length=500)
    description:  Optional[str] = None
    status:       TaskStatus   = TaskStatus.TODO
    priority:     TaskPriority = TaskPriority.MEDIUM
    source:       TaskSource   = TaskSource.MANUAL
    story_points: Optional[int] = Field(None, ge=1, le=100)

    # AI fields
    suggested_role:      Optional[str]       = None
    labels:              List[str]           = []
    acceptance_criteria: List[str]           = []

    # External
    jira_key: Optional[str] = None
    jira_url: Optional[str] = None

    # Relations
    project_id:  int
    sprint_id:   Optional[int] = None
    assigned_to: Optional[int] = None
    due_date:    Optional[datetime] = None


# ─── Create ──────────────────────────────────────────────────────────────────
class TaskCreate(TaskBase):
    pass


# ─── Bulk create (from PRD parser) ───────────────────────────────────────────
class TaskBulkCreate(BaseModel):
    project_id: int
    sprint_id:  Optional[int] = None
    tasks:      List[TaskCreate]


# ─── Update ──────────────────────────────────────────────────────────────────
class TaskUpdate(BaseModel):
    title:        Optional[str]          = None
    description:  Optional[str]          = None
    status:       Optional[TaskStatus]   = None
    priority:     Optional[TaskPriority] = None
    story_points: Optional[int]          = None
    sprint_id:    Optional[int]          = None
    assigned_to:  Optional[int]          = None
    due_date:     Optional[datetime]     = None
    labels:       Optional[List[str]]    = None
    jira_key:     Optional[str]          = None


# ─── Response ────────────────────────────────────────────────────────────────
class TaskResponse(TaskBase):
    id:          int
    assignee_name: Optional[str] = None
    started_at:  Optional[datetime] = None
    done_at:     Optional[datetime] = None
    created_at:  datetime
    updated_at:  Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Summary (for kanban cards / task lists) ──────────────────────────────────
class TaskSummary(BaseModel):
    id:           int
    title:        str
    status:       TaskStatus
    priority:     TaskPriority
    story_points: Optional[int] = None
    assigned_to:  Optional[int] = None
    due_date:     Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── PRD parse request ────────────────────────────────────────────────────────
class PRDParseRequest(BaseModel):
    project_id: int
    prd_text:   str  = Field(..., min_length=10)
    source:     str  = "prd"
    sprint_id:  Optional[int] = None
    auto_assign: bool = True
