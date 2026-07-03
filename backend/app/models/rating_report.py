from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import ReportType
from app.models.time import utc_now


class RatingReport(Base):
    __tablename__ = "ratings_reports"

    record_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.trip_id"), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=True)
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType), nullable=True)
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    from_user = relationship(
        "User",
        foreign_keys=[from_user_id],
        back_populates="ratings_given",
    )
    to_user = relationship(
        "User",
        foreign_keys=[to_user_id],
        back_populates="ratings_received",
    )
    trip = relationship("Trip", back_populates="rating_reports")
