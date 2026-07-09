from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import Gender, UserRole, VerificationStatus
from app.models.time import utc_now


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    student_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, index=True)
    gender: Mapped[Gender] = mapped_column(Enum(Gender), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False, default=5.0)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus),
        nullable=False,
        default=VerificationStatus.pending,
        index=True,
    )
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_verification_token_hash: Mapped[str] = mapped_column(String(128), nullable=True)
    email_verification_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    vehicles = relationship("Vehicle", back_populates="driver", cascade="all, delete-orphan")
    ride_requests = relationship("RideRequest", back_populates="rider", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="driver", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="payer")
    location_logs = relationship("LocationLog", back_populates="user")
    sos_events = relationship("SOSEvent", foreign_keys="SOSEvent.user_id", back_populates="user")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    ratings_given = relationship(
        "RatingReport",
        foreign_keys="RatingReport.from_user_id",
        back_populates="from_user",
    )
    ratings_received = relationship(
        "RatingReport",
        foreign_keys="RatingReport.to_user_id",
        back_populates="to_user",
    )
