from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import SOSStatus
from app.models.time import utc_now


class SOSEvent(Base):
    __tablename__ = "sos_events"

    sos_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.trip_id"), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[SOSStatus] = mapped_column(
        Enum(SOSStatus),
        nullable=False,
        default=SOSStatus.new,
        index=True,
    )
    triggered_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    resolved_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_admin_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=True, index=True)
    response_note: Mapped[str] = mapped_column(Text, nullable=True)
    status_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="sos_events")
    trip = relationship("Trip", back_populates="sos_events")
    assigned_admin = relationship("User", foreign_keys=[assigned_admin_id])
