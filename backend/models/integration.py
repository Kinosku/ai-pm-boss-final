from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SAEnum, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base


class IntegrationProvider(str, enum.Enum):
    GITHUB  = "github"
    SLACK   = "slack"
    JIRA    = "jira"
    LINEAR  = "linear"   # future
    NOTION  = "notion"   # future


class IntegrationStatus(str, enum.Enum):
    CONNECTED     = "connected"
    DISCONNECTED  = "disconnected"
    ERROR         = "error"
    PENDING       = "pending"


class Integration(Base):
    __tablename__ = "integrations"

    id         = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    provider   = Column(SAEnum(IntegrationProvider), nullable=False)
    status     = Column(SAEnum(IntegrationStatus), default=IntegrationStatus.DISCONNECTED, nullable=False)

    # Auth credentials (store encrypted in production)
    access_token  = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires = Column(DateTime(timezone=True), nullable=True)
    webhook_secret= Column(String(255), nullable=True)

    # Provider-specific config stored as JSON
    # GitHub:  { "repo": "org/repo", "installation_id": "..." }
    # Slack:   { "channel_id": "C...", "bot_user_id": "U..." }
    # Jira:    { "project_key": "PROJ", "base_url": "https://..." }
    config = Column(JSON, default=dict)

    # Sync metadata
    last_synced_at  = Column(DateTime(timezone=True), nullable=True)
    sync_error      = Column(Text, nullable=True)
    is_webhook_live = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # ─── Relationships ────────────────────────────────────────────────────────
    project = relationship("Project", back_populates="integrations")

    def __repr__(self):
        return f"<Integration id={self.id} provider={self.provider} status={self.status}>"
