from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SAEnum, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base


class SprintStatus(str, enum.Enum):
    PLANNED    = "planned"
    ACTIVE     = "active"
    COMPLETED  = "completed"
    CANCELLED  = "cancelled"


class Sprint(Base):
    __tablename__ = "sprints"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(255), nullable=False)        # e.g. "Sprint 12"
    goal       = Column(Text, nullable=True)
    status     = Column(SAEnum(SprintStatus), default=SprintStatus.PLANNED, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date   = Column(DateTime(timezone=True), nullable=True)

    # Velocity & points tracking
    points_planned   = Column(Integer, default=0, nullable=False)
    points_completed = Column(Integer, default=0, nullable=False)
    velocity         = Column(Float, nullable=True)    # story points per day

    # AI-computed health
    health_score = Column(Integer, nullable=True)      # 0–100

    # External reference
    jira_sprint_id = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # ─── Relationships ────────────────────────────────────────────────────────
    project     = relationship("Project",   back_populates="sprints")
    tasks       = relationship("Task",      back_populates="sprint")
    risk_alerts = relationship("RiskAlert", back_populates="sprint", cascade="all, delete-orphan")
    standups    = relationship("Standup",   back_populates="sprint", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Sprint id={self.id} name={self.name} status={self.status}>"
