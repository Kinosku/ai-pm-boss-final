from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SAEnum, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base


class RiskSeverity(str, enum.Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


class RiskCategory(str, enum.Enum):
    VELOCITY    = "velocity"
    PR_BOTTLENECK = "pr_bottleneck"
    BLOCKERS    = "blockers"
    TEAM        = "team"
    SCOPE_CREEP = "scope_creep"
    DEADLINE    = "deadline"
    OTHER       = "other"


class RiskStatus(str, enum.Enum):
    OPEN     = "open"
    RESOLVED = "resolved"
    DISMISSED= "dismissed"


class RiskAlert(Base):
    __tablename__ = "risk_alerts"

    id         = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    sprint_id  = Column(Integer, ForeignKey("sprints.id"),  nullable=True)

    # Alert content — mirrors UI risk cards
    alert_id        = Column(String(50),  nullable=True)     # e.g. "FAST-001"
    title           = Column(String(500), nullable=False)
    description     = Column(Text, nullable=True)
    recommendation  = Column(Text, nullable=True)
    severity        = Column(SAEnum(RiskSeverity), default=RiskSeverity.MEDIUM, nullable=False)
    category        = Column(SAEnum(RiskCategory), default=RiskCategory.OTHER,  nullable=False)
    status          = Column(SAEnum(RiskStatus),   default=RiskStatus.OPEN,     nullable=False)

    # Context data
    affected_developers = Column(JSON, default=list)   # list of developer names
    affected_tasks      = Column(JSON, default=list)   # list of task IDs

    # Detection metadata
    detected_by     = Column(String(100), default="Delay Prediction Agent")
    health_score    = Column(Integer, nullable=True)   # 0–100 at time of detection

    # Tracking
    is_slack_notified = Column(Boolean, default=False)
    resolved_at       = Column(DateTime(timezone=True), nullable=True)
    created_at        = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at        = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # ─── Relationships ────────────────────────────────────────────────────────
    project = relationship("Project", back_populates="risk_alerts")
    sprint  = relationship("Sprint",  back_populates="risk_alerts")

    def __repr__(self):
        return f"<RiskAlert id={self.id} severity={self.severity} title={self.title[:40]}>"
