from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base


class UserRole(str, enum.Enum):
    BOSS     = "boss"       # Project Manager / Admin — full dashboard access
    EMPLOYEE = "employee"   # Developer — personal task/PR/standup views


class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    full_name       = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role            = Column(SAEnum(UserRole), nullable=False, default=UserRole.EMPLOYEE)
    avatar_url      = Column(String(500), nullable=True)
    is_active       = Column(Boolean, default=True, nullable=False)
    is_verified     = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # ─── Relationships ────────────────────────────────────────────────────────
    developer     = relationship("Developer",    back_populates="user",    uselist=False)
    notifications = relationship("Notification", back_populates="user",    cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.role}>"
