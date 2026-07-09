from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.notification import Notification
from app.models.time import utc_now
from app.models.user import User
from app.schemas.notification import NotificationRead, NotificationUnreadCount


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/me", response_model=list[NotificationRead])
def list_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    unread_only: bool = Query(default=False),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=30, ge=1, le=100),
) -> list[Notification]:
    query = db.query(Notification).filter(Notification.user_id == current_user.user_id)
    if unread_only:
        query = query.filter(Notification.read_at.is_(None))
    return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/me/unread-count", response_model=NotificationUnreadCount)
def read_my_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationUnreadCount:
    unread_count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.user_id, Notification.read_at.is_(None))
        .count()
    )
    return NotificationUnreadCount(unread_count=unread_count)


@router.patch("/{notification_id}/read", response_model=NotificationRead)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Notification:
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if notification.read_at is None:
        notification.read_at = utc_now()
        db.add(notification)
        db.commit()
        db.refresh(notification)
    return notification


@router.patch("/me/read-all", response_model=NotificationUnreadCount)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationUnreadCount:
    unread_notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.user_id, Notification.read_at.is_(None))
        .all()
    )
    now = utc_now()
    for notification in unread_notifications:
        notification.read_at = now
        db.add(notification)
    db.commit()
    return NotificationUnreadCount(unread_count=0)
