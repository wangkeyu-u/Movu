from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_db
from app.models.enums import VerificationStatus
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    EmailVerificationRequest,
    LoginRequest,
    MessageResponse,
    ResendVerificationRequest,
)
from app.schemas.user import UserRead, UserRegister
from app.services.email_verification import (
    issue_email_verification,
    send_verification_email,
    verify_email_token,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegister, db: Session = Depends(get_db)) -> User:
    email = str(payload.email).lower().strip()
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    if payload.student_id:
        existing_student = db.query(User).filter(User.student_id == payload.student_id).first()
        if existing_student is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Student or staff ID is already registered",
            )

    user = User(
        name=payload.name,
        email=email,
        student_id=payload.student_id,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
        gender=payload.gender,
        verification_status=VerificationStatus.pending,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = issue_email_verification(db, user)
    send_verification_email(user, token)
    return user


@router.post("/verify-email", response_model=UserRead)
def verify_email(payload: EmailVerificationRequest, db: Session = Depends(get_db)) -> User:
    return verify_email_token(db, payload.token)


@router.post("/resend-verification", response_model=MessageResponse)
def resend_verification(
    payload: ResendVerificationRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    email = str(payload.email).lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        return MessageResponse(message="If the account exists, a verification email has been sent")
    if user.email_verified:
        return MessageResponse(message="Email is already verified")
    token = issue_email_verification(db, user)
    send_verification_email(user, token)
    return MessageResponse(message="If the account exists, a verification email has been sent")


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    email = str(payload.email).lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if user.is_banned:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is banned")
    if not user.email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email is not verified")

    token = create_access_token(subject=user.email)
    return AuthResponse(access_token=token, user=user)
