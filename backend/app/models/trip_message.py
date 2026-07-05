from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.time import utc_now


class TripMessage(Base):
    __tablename__ = "trip_messages"

    message_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.trip_id"), nullable=False, index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    body: Mapped[str] = mapped_column(String(600), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    trip = relationship("Trip", back_populates="messages")
    sender = relationship("User")
