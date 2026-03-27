from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from models.notification import NotificationType, NotificationPriority


# ─── Base ────────────────────────────────────────────────────────────────────
class NotificationBase(BaseModel):
    user_id:      int
    type:         NotificationType     = NotificationType.SYSTEM
    priority:     NotificationPriority = NotificationPriority.MEDIUM
    title:        str                  = Field(..., min_length=2, max_length=500)
    message:      Optional[str]        = None
    action_url:   Optional[str]        = None
    action_label: Optional[str]        = None
    source_type:  Optional[str]        = None
    source_id:    Optional[int]        = None


# ─── Create ──────────────────────────────────────────────────────────────────
class NotificationCreate(NotificationBase):
    pass


# ─── Bulk create (for broadcasting to multiple users) ────────────────────────
class NotificationBroadcast(BaseModel):
    user_ids:     List[int]
    type:         NotificationType     = NotificationType.SYSTEM
    priority:     NotificationPriority = NotificationPriority.MEDIUM
    title:        str
    message:      Optional[str]        = None
    action_url:   Optional[str]        = None
    action_label: Optional[str]        = None
    source_type:  Optional[str]        = None
    source_id:    Optional[int]        = None


# ─── Update ──────────────────────────────────────────────────────────────────
class NotificationUpdate(BaseModel):
    is_read: bool = True
    read_at: Optional[datetime] = None


# ─── Response ────────────────────────────────────────────────────────────────
class NotificationResponse(NotificationBase):
    id:         int
    is_read:    bool
    read_at:    Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Unread count (for nav badge) ─────────────────────────────────────────────
class NotificationCountResponse(BaseModel):
    total:    int
    unread:   int
    by_type:  dict = {}
