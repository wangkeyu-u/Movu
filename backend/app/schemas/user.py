from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import Gender, UserRole, VerificationStatus


ALLOWED_TAYLORS_EMAIL_DOMAINS = ("@sd.taylors.edu.my", "@taylors.edu.my")


def is_taylors_email(email: str) -> bool:
    normalized = email.lower().strip()
    return normalized.endswith(ALLOWED_TAYLORS_EMAIL_DOMAINS)


class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    student_id: Optional[str] = Field(default=None, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole
    gender: Gender

    @field_validator("email")
    @classmethod
    def validate_taylors_email(cls, value: EmailStr) -> EmailStr:
        if not is_taylors_email(str(value)):
            raise ValueError("Email must be a Taylor's University email")
        return value

    @field_validator("role")
    @classmethod
    def validate_public_role(cls, value: UserRole) -> UserRole:
        if value == UserRole.admin:
            raise ValueError("Admin accounts cannot be created through public registration")
        return value


class UserRead(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    student_id: Optional[str]
    role: UserRole
    gender: Gender
    rating: float
    verification_status: VerificationStatus
    email_verified: bool
    is_banned: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserVerificationUpdate(BaseModel):
    verification_status: VerificationStatus
