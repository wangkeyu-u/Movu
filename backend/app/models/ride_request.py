from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import GenderPreference, RideRequestStatus
from app.models.time import utc_now


class RideRequest(Base):
    __tablename__ = "ride_requests"

    request_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rider_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    origin: Mapped[str] = mapped_column(String(255), nullable=False)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    origin_latitude: Mapped[float] = mapped_column(Float, nullable=True)
    origin_longitude: Mapped[float] = mapped_column(Float, nullable=True)
    destination_latitude: Mapped[float] = mapped_column(Float, nullable=True)
    destination_longitude: Mapped[float] = mapped_column(Float, nullable=True)
    preferred_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    passenger_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    gender_preference: Mapped[GenderPreference] = mapped_column(
        Enum(GenderPreference),
        nullable=False,
        default=GenderPreference.none,
    )
    distance_km: Mapped[float] = mapped_column(Float, nullable=True)
    status: Mapped[RideRequestStatus] = mapped_column(
        Enum(RideRequestStatus),
        nullable=False,
        default=RideRequestStatus.pending,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    rider = relationship("User", back_populates="ride_requests")
    matches = relationship("RideMatch", back_populates="ride_request", cascade="all, delete-orphan")
