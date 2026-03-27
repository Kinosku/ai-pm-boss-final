from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from models.standup import StandupStatus


# ─── Base ────────────────────────────────────────────────────────────────────
class StandupBase(BaseModel):
    project_id:   int
    sprint_id:    Optional[int] = None
    developer_id: Optional[int] = None
    standup_date: datetime
    done:         List[str] = []
    doing:        List[str] = []
    blocked:      List[str] = []
    raw_message:  Optional[str] = None


# ─── Create (individual dev submits update) ───────────────────────────────────
class StandupCreate(StandupBase):
    pass


# ─── Slack update (raw message from Slack parser) ────────────────────────────
class StandupSlackUpdate(BaseModel):
    project_id:   int
    developer_id: int
    slack_user_id:str
    raw_message:  str = Field(..., min_length=1)
    channel_id:   Optional[str] = None


# ─── Update ──────────────────────────────────────────────────────────────────
class StandupUpdate(BaseModel):
    done:            Optional[List[str]] = None
    doing:           Optional[List[str]] = None
    blocked:         Optional[List[str]] = None
    status:          Optional[StandupStatus] = None
    summary_text:    Optional[str]       = None
    slack_message_ts:Optional[str]       = None


# ─── Response ────────────────────────────────────────────────────────────────
class StandupResponse(StandupBase):
    id:              int
    status:          StandupStatus
    is_summary:      bool
    summary_text:    Optional[str] = None
    blockers_json:   List[dict]    = []
    slack_message_ts:Optional[str] = None
    slack_channel:   Optional[str] = None
    created_at:      datetime
    updated_at:      Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Summary response (AI-generated team standup) ─────────────────────────────
class StandupSummaryResponse(BaseModel):
    standup_date:         str
    sprint_day:           str
    summary_text:         str
    blockers:             List[dict] = []
    developers_reported:  List[str]  = []
    developers_missing:   List[str]  = []
    overall_sentiment:    str        = "neutral"
    slack_channel:        Optional[str] = None


# ─── Trigger standup collection ───────────────────────────────────────────────
class StandupTriggerRequest(BaseModel):
    project_id: int
    channel_id: str
    sprint_id:  Optional[int] = None
