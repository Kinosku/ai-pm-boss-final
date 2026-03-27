from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base


class ProjectStatus(str, enum.Enum):
    ACTIVE    = "active"
    ON_HOLD   = "on_hold"
    COMPLETED = "completed"
    ARCHIVED  = "archived"


class Project(Base):
    __tablename__ = "projects"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status      = Column(SAEnum(ProjectStatus), default=ProjectStatus.ACTIVE, nullable=False)
    owner_id    = Column(Integer, ForeignKey("users.id"), nullable=False)

    # External identifiers
    github_repo   = Column(String(255), nullable=True)   # e.g. "org/repo-name"
    jira_project  = Column(String(100), nullable=True)   # e.g. "PROJ"
    slack_channel = Column(String(100), nullable=True)   # e.g. "#dev-team"

    is_active  = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # ─── Relationships ────────────────────────────────────────────────────────
    owner        = relationship("User",         foreign_keys=[owner_id])
    sprints      = relationship("Sprint",       back_populates="project", cascade="all, delete-orphan")
    tasks        = relationship("Task",         back_populates="project", cascade="all, delete-orphan")
    risk_alerts  = relationship("RiskAlert",    back_populates="project", cascade="all, delete-orphan")
    standups     = relationship("Standup",      back_populates="project", cascade="all, delete-orphan")
    pull_requests= relationship("PullRequest",  back_populates="project", cascade="all, delete-orphan")
    integrations = relationship("Integration",  back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project id={self.id} name={self.name} status={self.status}>"
