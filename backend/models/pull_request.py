from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SAEnum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base


class PRStatus(str, enum.Enum):
    OPEN     = "open"
    IN_REVIEW= "in_review"
    APPROVED = "approved"
    MERGED   = "merged"
    CLOSED   = "closed"


class PRReviewStatus(str, enum.Enum):
    PENDING   = "pending"
    APPROVED  = "approved"
    CHANGES_REQUESTED = "changes_requested"


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id         = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    task_id    = Column(Integer, ForeignKey("tasks.id"),    nullable=True)   # AI-mapped
    author_id  = Column(Integer, ForeignKey("developers.id"), nullable=True)

    # GitHub data
    github_pr_number = Column(Integer, nullable=False, index=True)
    github_pr_id     = Column(String(100), nullable=True)
    title            = Column(String(500), nullable=False)
    description      = Column(Text, nullable=True)
    status           = Column(SAEnum(PRStatus), default=PRStatus.OPEN, nullable=False)
    review_status    = Column(SAEnum(PRReviewStatus), default=PRReviewStatus.PENDING, nullable=True)

    # Branch info
    head_branch = Column(String(255), nullable=True)
    base_branch = Column(String(100), default="main", nullable=True)
    github_url  = Column(String(500), nullable=True)

    # Metrics
    additions    = Column(Integer, default=0)
    deletions    = Column(Integer, default=0)
    files_changed= Column(Integer, default=0)
    is_stale     = Column(Boolean, default=False)   # open > 48 hours

    opened_at  = Column(DateTime(timezone=True), nullable=True)
    merged_at  = Column(DateTime(timezone=True), nullable=True)
    closed_at  = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # ─── Relationships ────────────────────────────────────────────────────────
    project = relationship("Project",   back_populates="pull_requests")
    author  = relationship("Developer", foreign_keys=[author_id])

    def __repr__(self):
        return f"<PullRequest #{self.github_pr_number} status={self.status}>"
