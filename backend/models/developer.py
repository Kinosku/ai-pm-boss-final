from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Enum as SAEnum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base


class DeveloperRole(str, enum.Enum):
    BACKEND   = "backend"
    FRONTEND  = "frontend"
    FULLSTACK = "fullstack"
    DEVOPS    = "devops"
    QA        = "qa"


class Developer(Base):
    __tablename__ = "developers"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    project_id   = Column(Integer, ForeignKey("projects.id"), nullable=True)

    role         = Column(SAEnum(DeveloperRole), default=DeveloperRole.FULLSTACK, nullable=False)
    skills       = Column(JSON, default=list)        # ["python", "fastapi", "react", ...]
    is_available = Column(Boolean, default=True, nullable=False)

    # Performance metrics (updated by AI agents)
    velocity        = Column(Float, default=0.0)     # avg story points per sprint
    open_tasks      = Column(Integer, default=0)     # live count
    total_tasks_done= Column(Integer, default=0)
    total_prs_merged= Column(Integer, default=0)

    # External identifiers
    github_username = Column(String(100), nullable=True, index=True)
    slack_user_id   = Column(String(100), nullable=True)
    jira_account_id = Column(String(100), nullable=True)

    last_commit_at  = Column(DateTime(timezone=True), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # ─── Relationships ────────────────────────────────────────────────────────
    user     = relationship("User",        back_populates="developer")
    tasks    = relationship("Task",        back_populates="assignee")
    standups = relationship("Standup",     back_populates="developer")

    def __repr__(self):
        return f"<Developer id={self.id} role={self.role} velocity={self.velocity}>"
