from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from models.sprint import SprintStatus


# ─── Base ────────────────────────────────────────────────────────────────────
class SprintBase(BaseModel):
    name:       str           = Field(..., min_length=2, max_length=255)
    goal:       Optional[str] = None
    status:     SprintStatus  = SprintStatus.PLANNED
    project_id: int
    start_date: Optional[datetime] = None
    end_date:   Optional[datetime] = None
    points_planned: int = Field(default=0, ge=0)
    jira_sprint_id: Optional[str] = None


# ─── Create ──────────────────────────────────────────────────────────────────
class SprintCreate(SprintBase):
    pass


# ─── Update ──────────────────────────────────────────────────────────────────
class SprintUpdate(BaseModel):
    name:            Optional[str]          = None
    goal:            Optional[str]          = None
    status:          Optional[SprintStatus] = None
    start_date:      Optional[datetime]     = None
    end_date:        Optional[datetime]     = None
    points_planned:  Optional[int]          = None
    points_completed:Optional[int]          = None
    health_score:    Optional[int]          = Field(None, ge=0, le=100)


# ─── Response ────────────────────────────────────────────────────────────────
class SprintResponse(SprintBase):
    id:               int
    points_completed: int
    velocity:         Optional[float] = None
    health_score:     Optional[int]   = None
    created_at:       datetime
    updated_at:       Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Summary (for dashboards) ─────────────────────────────────────────────────
class SprintSummary(BaseModel):
    id:               int
    name:             str
    status:           SprintStatus
    points_planned:   int
    points_completed: int
    health_score:     Optional[int] = None
    end_date:         Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Sprint stats (for velocity chart on reports page) ───────────────────────
class SprintStats(BaseModel):
    sprint_id:        int
    sprint_name:      str
    points_planned:   int
    points_completed: int
    velocity:         Optional[float] = None
    health_score:     Optional[int]   = None
    task_counts: dict = {}   # {"todo": N, "in_progress": N, "done": N, "blocked": N}
