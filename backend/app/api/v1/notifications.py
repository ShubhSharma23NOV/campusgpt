"""Notification management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional

from app.core.database import get_db
from app.core.security import require_student, require_admin
from app.models.notification import Notification

router = APIRouter()


@router.get("/my")
async def get_my_notifications(
    payload: dict = Depends(require_student),
    db: AsyncSession = Depends(get_db),
    unread_only: bool = Query(default=False),
    limit: int = Query(default=20, le=100),
):
    """Get notifications for the logged-in student."""
    student_id = int(payload["sub"])

    query = select(Notification).where(
        and_(
            Notification.user_id == student_id,
            Notification.user_type == "student",
        )
    )

    if unread_only:
        query = query.where(Notification.is_read == False)

    query = query.order_by(Notification.created_at.desc()).limit(limit)
    result = await db.execute(query)
    notifications = result.scalars().all()

    unread_count = sum(1 for n in notifications if not n.is_read)

    return {
        "unread_count": unread_count,
        "notifications": [
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "message": n.message,
                "action_url": n.action_url,
                "is_read": n.is_read,
                "read_at": str(n.read_at) if n.read_at else None,
                "created_at": str(n.created_at),
            }
            for n in notifications
        ],
    }


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    payload: dict = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Mark a notification as read."""
    student_id = int(payload["sub"])

    result = await db.execute(
        select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.user_id == student_id,
                Notification.user_type == "student",
            )
        )
    )
    notif = result.scalar_one_or_none()

    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.is_read = True
    notif.read_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "Marked as read"}


@router.post("/read-all")
async def mark_all_read(
    payload: dict = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read."""
    student_id = int(payload["sub"])

    await db.execute(
        update(Notification)
        .where(
            and_(
                Notification.user_id == student_id,
                Notification.user_type == "student",
                Notification.is_read == False,
            )
        )
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    await db.commit()
    return {"message": "All notifications marked as read"}


class CreateNotificationRequest(BaseModel):
    user_id: int
    user_type: str = "student"
    notification_type: str
    title: str
    message: str
    action_url: Optional[str] = None


@router.post("/send", status_code=201)
async def send_notification(
    req: CreateNotificationRequest,
    payload: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Send a notification to a student (admin only)."""
    notif = Notification(
        user_id=req.user_id,
        user_type=req.user_type,
        type=req.notification_type,
        title=req.title,
        message=req.message,
        action_url=req.action_url,
        channel="in_app",
        sent_at=datetime.now(timezone.utc),
    )
    db.add(notif)
    await db.commit()

    return {"message": "Notification sent", "id": notif.id}


@router.post("/broadcast", status_code=201)
async def broadcast_notification(
    req: CreateNotificationRequest,
    payload: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Broadcast a notification to all students (admin only)."""
    from app.models.student import Student
    from sqlalchemy import select

    result = await db.execute(select(Student.id).where(Student.is_active == True))
    student_ids = [row[0] for row in result.all()]

    notifications = [
        Notification(
            user_id=sid,
            user_type="student",
            type=req.notification_type,
            title=req.title,
            message=req.message,
            action_url=req.action_url,
            channel="in_app",
            sent_at=datetime.now(timezone.utc),
        )
        for sid in student_ids
    ]
    db.add_all(notifications)
    await db.commit()

    return {"message": f"Broadcast sent to {len(student_ids)} students"}
