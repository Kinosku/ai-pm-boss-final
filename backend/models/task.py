from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SAEnum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base


class TaskStatus(str, enum.Enum):
    BACKLOG      = "backlog"
    TODO         = "todo"
    IN_PROGRESS  = "in_progress"
    IN_REVIEW    = "in_review"
    BLOCKED      = "blocked"
    DONE         = "done"


class TaskPriority(str, enum.Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


class TaskSource(str, enum.Enum):
    PRD      = "prd"
    SLACK    = "slack"
    MANUAL   = "manual"
    JIRA     = "jira"


class Task(Base):
    __tablename__ = "tasks"

    id           = Column(Integer, primary_key=True, index=True)
    title        = Column(String(500), nullable=False)
    description  = Column(Text, nullable=True)
    status       = Column(SAEnum(TaskStatus),   default=TaskStatus.TODO,   nullable=False)
    priority     = Column(SAEnum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    source       = Column(SAEnum(TaskSource),   default=TaskSource.MANUAL, nullable=False)
    story_points = Column(Integer, nullable=True)

    # AI-generated fields
    suggested_role       = Column(String(100), nullable=True)   # backend/frontend/fullstack
    labels               = Column(JSON, default=list)           # ["auth", "api", ...]
    acceptance_criteria  = Column(JSON, default=list)           # list of strings

    # External references
    jira_key     = Column(String(50),  nullable=True, index=True)  # e.g. "PROJ-42"
    jira_url     = Column(String(500), nullable=True)

    # FK relationships
    project_id   = Column(Integer, ForeignKey("projects.id"), nullable=False)
    sprint_id    = Column(Integer, ForeignKey("sprints.id"),  nullable=True)
    assigned_to  = Column(Integer, ForeignKey("developers.id"), nullable=True)

    due_date   = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    done_at    = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # ─── Relationships ────────────────────────────────────────────────────────
    project   = relationship("Project",   back_populates="tasks")
    sprint    = relationship("Sprint",    back_populates="tasks")
    assignee  = relationship("Developer", back_populates="tasks")

    def __repr__(self):
        return f"<Task id={self.id} title={self.title[:40]} status={self.status}>"
