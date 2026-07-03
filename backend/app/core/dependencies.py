from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import UserRole, VerificationStatus
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
    except ValueError as exc:
        raise credentials_error from exc

    if not isinstance(email, str):
        raise credentials_error

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_error
    if user.is_banned:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is banned")
    return user


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return current_user

    return role_dependency


def require_approved_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role == UserRole.admin:
        return current_user
    if not current_user.email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email is not verified")
    if current_user.verification_status != VerificationStatus.approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is not approved")
    return current_user


def require_approved_roles(*roles: UserRole) -> Callable[[User], User]:
    def role_dependency(current_user: User = Depends(require_approved_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return current_user

    return role_dependency
