from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.time import utc_now
from app.models.user import User
from app.services.email import send_email


def hash_verification_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def issue_email_verification(db: Session, user: User) -> str:
    token = token_urlsafe(48)
    user.email_verification_token_hash = hash_verification_token(token)
    user.email_verification_expires_at = utc_now() + timedelta(
        minutes=settings.email_verification_expire_minutes
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return token


def send_verification_email(user: User, token: str) -> None:
    verification_url = f"{settings.frontend_base_url}/verify-email?token={token}"
    body = (
        f"Hi {user.name},\n\n"
        "Verify your MovU account by opening this link:\n"
        f"{verification_url}\n\n"
        "If you did not create this account, you can ignore this email."
    )
    send_email(to_email=user.email, subject="Verify your MovU account", body=body)


def verify_email_token(db: Session, token: str) -> User:
    token_hash = hash_verification_token(token)
    user = (
        db.query(User)
        .filter(User.email_verification_token_hash == token_hash)
        .first()
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token")
    expires_at = user.email_verification_expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at is None or expires_at < utc_now():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification token expired")

    user.email_verified = True
    user.email_verification_token_hash = None
    user.email_verification_expires_at = None
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
