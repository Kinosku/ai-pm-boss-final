from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from models.risk_alert import RiskSeverity, RiskCategory, RiskStatus


# ─── Base ────────────────────────────────────────────────────────────────────
class RiskAlertBase(BaseModel):
    project_id:    int
    sprint_id:     Optional[int]  = None
    alert_id:      Optional[str]  = None
    title:         str            = Field(..., min_length=5, max_length=500)
    description:   Optional[str]  = None
    recommendation:Optional[str]  = None
    severity:      RiskSeverity   = RiskSeverity.MEDIUM
    category:      RiskCategory   = RiskCategory.OTHER
    status:        RiskStatus     = RiskStatus.OPEN
    affected_developers: List[str] = []
    affected_tasks:      List[int] = []
    detected_by:   str             = "Delay Prediction Agent"
    health_score:  Optional[int]   = Field(None, ge=0, le=100)


# ─── Create ──────────────────────────────────────────────────────────────────
class RiskAlertCreate(RiskAlertBase):
    pass


# ─── Update ──────────────────────────────────────────────────────────────────
class RiskAlertUpdate(BaseModel):
    status:            Optional[RiskStatus]   = None
    recommendation:    Optional[str]          = None
    is_slack_notified: Optional[bool]         = None
    resolved_at:       Optional[datetime]     = None


# ─── Response ────────────────────────────────────────────────────────────────
class RiskAlertResponse(RiskAlertBase):
    id:                int
    is_slack_notified: bool
    resolved_at:       Optional[datetime] = None
    created_at:        datetime
    updated_at:        Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Summary (for risk cards on boss dashboard) ───────────────────────────────
class RiskAlertSummary(BaseModel):
    id:           int
    title:        str
    severity:     RiskSeverity
    category:     RiskCategory
    status:       RiskStatus
    detected_by:  str
    created_at:   datetime

    model_config = {"from_attributes": True}


# ─── Analyze request (trigger AI risk analysis) ───────────────────────────────
class RiskAnalyzeRequest(BaseModel):
    project_id:       int
    sprint_id:        int
    project_name:     str
    sprint_name:      str
    sprint_end_date:  str            # ISO date string
    total_tasks:      int = 0
    completed_tasks:  int = 0
    in_progress_tasks:int = 0
    blocked_tasks:    int = 0
    last_velocity:    float = 0
    current_velocity: float = 0
    stale_prs:        int = 0
    inactive_devs:    int = 0


# ─── Risk counts (for dashboard stat cards) ───────────────────────────────────
class RiskCounts(BaseModel):
    critical: int = 0
    high:     int = 0
    medium:   int = 0
    low:      int = 0
    total:    int = 0
