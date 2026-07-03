from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import MatchStatus
from app.models.time import utc_now


class RideMatch(Base):
    __tablename__ = "matches"

    match_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.trip_id"), nullable=False, index=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("ride_requests.request_id"),
        nullable=False,
        index=True,
    )
    rider_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    score_breakdown: Mapped[dict] = mapped_column(JSON, nullable=True)
    reasons: Mapped[list] = mapped_column(JSON, nullable=True)
    status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus),
        nullable=False,
        default=MatchStatus.recommended,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    trip = relationship("Trip", back_populates="matches")
    ride_request = relationship("RideRequest", back_populates="matches")
    rider = relationship("User")
    payments = relationship("Payment", back_populates="match", cascade="all, delete-orphan")
