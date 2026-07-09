from collections.abc import Iterable

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.enums import UserRole
from app.models.user import User


def create_notification(
    db: Session,
    *,
    user_id: int,
    title: str,
    body: str,
    category: str = "system",
    entity_type: str | None = None,
    entity_id: int | str | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=title,
        body=body,
        category=category,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
    )
    db.add(notification)
    return notification


def create_notifications(
    db: Session,
    *,
    user_ids: Iterable[int],
    title: str,
    body: str,
    category: str = "system",
    entity_type: str | None = None,
    entity_id: int | str | None = None,
) -> None:
    for user_id in set(user_ids):
        create_notification(
            db,
            user_id=user_id,
            title=title,
            body=body,
            category=category,
            entity_type=entity_type,
            entity_id=entity_id,
        )


def notify_admins(
    db: Session,
    *,
    title: str,
    body: str,
    category: str = "operations",
    entity_type: str | None = None,
    entity_id: int | str | None = None,
) -> None:
    admin_ids = [
        user.user_id
        for user in db.query(User.user_id)
        .filter(User.role == UserRole.admin, User.is_banned.is_(False))
        .all()
    ]
    create_notifications(
        db,
        user_ids=admin_ids,
        title=title,
        body=body,
        category=category,
        entity_type=entity_type,
        entity_id=entity_id,
    )
