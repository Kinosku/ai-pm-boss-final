from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SAEnum, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base


class StandupStatus(str, enum.Enum):
    PENDING   = "pending"    # waiting for developer updates
    COLLECTED = "collected"  # all updates in
    POSTED    = "posted"     # summary posted to Slack


class Standup(Base):
    __tablename__ = "standups"

    id           = Column(Integer, primary_key=True, index=True)
    project_id   = Column(Integer, ForeignKey("projects.id"), nullable=False)
    sprint_id    = Column(Integer, ForeignKey("sprints.id"),  nullable=True)
    developer_id = Column(Integer, ForeignKey("developers.id"), nullable=True)  # null = team summary

    status       = Column(SAEnum(StandupStatus), default=StandupStatus.PENDING, nullable=False)
    standup_date = Column(DateTime(timezone=True), nullable=False)

    # Individual developer update fields
    done    = Column(JSON, default=list)    # list of strings: what was done yesterday
    doing   = Column(JSON, default=list)    # list of strings: what's planned today
    blocked = Column(JSON, default=list)    # list of strings: blockers

    # AI-generated team summary (only on summary row)
    is_summary     = Column(Boolean, default=False)
    summary_text   = Column(Text, nullable=True)    # Slack-ready formatted summary
    blockers_json  = Column(JSON, default=list)     # structured blocker objects from LLM

    # Slack delivery
    slack_message_ts = Column(String(100), nullable=True)    # Slack message timestamp
    slack_channel    = Column(String(100), nullable=True)

    # Developer raw input
    raw_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # ─── Relationships ────────────────────────────────────────────────────────
    project   = relationship("Project",   back_populates="standups")
    sprint    = relationship("Sprint",    back_populates="standups")
    developer = relationship("Developer", back_populates="standups")

    def __repr__(self):
        return f"<Standup id={self.id} date={self.standup_date} summary={self.is_summary}>"
