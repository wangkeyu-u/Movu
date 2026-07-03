from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import VerificationStatus
from app.models.time import utc_now


class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    plate_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    vehicle_model: Mapped[str] = mapped_column(String(120), nullable=False)
    seat_count: Mapped[int] = mapped_column(Integer, nullable=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus),
        nullable=False,
        default=VerificationStatus.pending,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    driver = relationship("User", back_populates="vehicles")
