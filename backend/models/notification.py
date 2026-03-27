from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SAEnum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base


class NotificationType(str, enum.Enum):
    RISK_ALERT    = "risk_alert"     # ⚠️ AI detected a sprint risk
    AGENT_ACTION  = "agent_action"   # 🤖 An AI agent completed an action
    PR_UPDATE     = "pr_update"      # 🔀 PR opened / merged / review requested
    REPORT_READY  = "report_ready"   # 📊 Weekly/sprint report generated
    TASK_ASSIGNED = "task_assigned"  # ✅ AI Boss assigned a task to you
    BLOCKER       = "blocker"        # 🚨 A blocker was reported
    SYSTEM        = "system"         # ℹ️ General system notification


class NotificationPriority(str, enum.Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


class Notification(Base):
    __tablename__ = "notifications"

    id      = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Content — mirrors notification cards in UI
    type        = Column(SAEnum(NotificationType),     default=NotificationType.SYSTEM, nullable=False)
    priority    = Column(SAEnum(NotificationPriority), default=NotificationPriority.MEDIUM, nullable=False)
    title       = Column(String(500), nullable=False)
    message     = Column(Text, nullable=True)

    # Action link
    action_url   = Column(String(500), nullable=True)    # e.g. "/risks/42"
    action_label = Column(String(100), nullable=True)    # e.g. "View Alert"

    # Source context
    source_type = Column(String(100), nullable=True)   # e.g. "risk_alert", "agent"
    source_id   = Column(Integer, nullable=True)       # FK to source record

    # State
    is_read    = Column(Boolean, default=False, nullable=False)
    read_at    = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ─── Relationships ────────────────────────────────────────────────────────
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification id={self.id} type={self.type} user={self.user_id} read={self.is_read}>"
