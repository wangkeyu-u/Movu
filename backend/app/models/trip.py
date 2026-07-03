from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import TripStatus
from app.models.time import utc_now


class Trip(Base):
    __tablename__ = "trips"

    trip_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    origin: Mapped[str] = mapped_column(String(255), nullable=False)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    origin_latitude: Mapped[float] = mapped_column(Float, nullable=True)
    origin_longitude: Mapped[float] = mapped_column(Float, nullable=True)
    destination_latitude: Mapped[float] = mapped_column(Float, nullable=True)
    destination_longitude: Mapped[float] = mapped_column(Float, nullable=True)
    departure_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    available_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    total_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[TripStatus] = mapped_column(
        Enum(TripStatus),
        nullable=False,
        default=TripStatus.posted,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    driver = relationship("User", back_populates="trips")
    matches = relationship("RideMatch", back_populates="trip", cascade="all, delete-orphan")
    location_logs = relationship("LocationLog", back_populates="trip", cascade="all, delete-orphan")
    sos_events = relationship("SOSEvent", back_populates="trip")
    rating_reports = relationship("RatingReport", back_populates="trip")
