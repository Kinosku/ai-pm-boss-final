from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime

from database import get_db
from models.notification import Notification, NotificationType
from models.user import User
from schemas.notification import (
    NotificationCreate, NotificationUpdate,
    NotificationResponse, NotificationCountResponse,
    NotificationBroadcast,
)
from routers.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(
    unread_only: bool              = Query(False),
    type:        Optional[NotificationType] = Query(None),
    limit:       int               = Query(20, ge=1, le=100),
    db: AsyncSession               = Depends(get_db),
    current_user: User             = Depends(get_current_user),
):
    q = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only: q = q.where(Notification.is_read == False)
    if type:        q = q.where(Notification.type == type)
    result = await db.execute(q.order_by(Notification.created_at.desc()).limit(limit))
    return result.scalars().all()


@router.get("/count", response_model=NotificationCountResponse)
async def get_notification_count(
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unread badge count for the navbar."""
    total_result = await db.execute(
        select(func.count(Notification.id)).where(Notification.user_id == current_user.id)
    )
    unread_result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )
    # Count by type
    type_result = await db.execute(
        select(Notification.type, func.count(Notification.id))
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .group_by(Notification.type)
    )
    by_type = {row[0]: row[1] for row in type_result.all()}

    return NotificationCountResponse(
        total   = total_result.scalar() or 0,
        unread  = unread_result.scalar() or 0,
        by_type = by_type,
    )


@router.post("/", response_model=NotificationResponse)
async def create_notification(
    payload: NotificationCreate,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = Notification(**payload.model_dump())
    db.add(notif)
    await db.flush()
    await db.refresh(notif)
    return notif


@router.post("/broadcast")
async def broadcast_notification(
    payload: NotificationBroadcast,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send same notification to multiple users (used by agents)."""
    created = []
    for uid in payload.user_ids:
        notif = Notification(
            user_id      = uid,
            type         = payload.type,
            priority     = payload.priority,
            title        = payload.title,
            message      = payload.message,
            action_url   = payload.action_url,
            action_label = payload.action_label,
            source_type  = payload.source_type,
            source_id    = payload.source_id,
        )
        db.add(notif)
        created.append(notif)
    await db.flush()
    return {"sent": len(created)}


@router.patch("/{notif_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notif_id: int,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification).where(
            Notification.id      == notif_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    notif.read_at = datetime.utcnow()
    await db.flush()
    await db.refresh(notif)
    return notif


@router.post("/mark-all-read")
async def mark_all_read(
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )
    notifs = result.scalars().all()
    now = datetime.utcnow()
    for n in notifs:
        n.is_read = True
        n.read_at = now
    await db.flush()
    return {"marked_read": len(notifs)}
