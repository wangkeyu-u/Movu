from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserRead, UserVerificationUpdate
from app.services.audit import write_audit_log
from app.services.notifications import create_notification


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}/verification", response_model=UserRead)
def update_user_verification(
    user_id: int,
    payload: UserVerificationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles(UserRole.admin)),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.verification_status = payload.verification_status
    write_audit_log(
        db,
        actor=admin_user,
        action="user.verification_updated",
        entity_type="user",
        entity_id=user.user_id,
        request=request,
        metadata={"verification_status": payload.verification_status.value},
    )
    create_notification(
        db,
        user_id=user.user_id,
        title="Account review updated",
        body=f"Your MovU account verification is now {payload.verification_status.value}.",
        category="verification",
        entity_type="user",
        entity_id=user.user_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/ban", response_model=UserRead)
def ban_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles(UserRole.admin)),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.role == UserRole.admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin users cannot be banned")

    user.is_banned = True
    create_notification(
        db,
        user_id=user.user_id,
        title="Account access suspended",
        body="Your MovU account has been banned by an administrator.",
        category="verification",
        entity_type="user",
        entity_id=user.user_id,
    )
    write_audit_log(
        db,
        actor=admin_user,
        action="user.banned",
        entity_type="user",
        entity_id=user.user_id,
        request=request,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/unban", response_model=UserRead)
def unban_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles(UserRole.admin)),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_banned = False
    create_notification(
        db,
        user_id=user.user_id,
        title="Account access restored",
        body="Your MovU account has been unbanned.",
        category="verification",
        entity_type="user",
        entity_id=user.user_id,
    )
    write_audit_log(
        db,
        actor=admin_user,
        action="user.unbanned",
        entity_type="user",
        entity_id=user.user_id,
        request=request,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
