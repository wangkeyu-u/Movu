from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import MatchStatus, TripStatus, UserRole
from app.models.location_log import LocationLog
from app.models.match import RideMatch
from app.models.trip import Trip
from app.models.user import User


def user_can_view_trip_location(db: Session, user: User, trip: Trip) -> bool:
    if user.role == UserRole.admin:
        return True
    if user.role == UserRole.driver and trip.driver_id == user.user_id:
        return True
    if user.role == UserRole.rider:
        return (
            db.query(RideMatch)
            .filter(
                RideMatch.trip_id == trip.trip_id,
                RideMatch.rider_id == user.user_id,
                RideMatch.status == MatchStatus.confirmed,
            )
            .first()
            is not None
        )
    return False


def record_driver_location(
    db: Session,
    *,
    trip: Trip,
    user: User,
    latitude: float,
    longitude: float,
) -> LocationLog:
    if user.role != UserRole.driver or trip.driver_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the trip driver can send location")
    if trip.status != TripStatus.ongoing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trip must be ongoing")

    log = LocationLog(
        trip_id=trip.trip_id,
        user_id=user.user_id,
        latitude=latitude,
        longitude=longitude,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_latest_trip_location(db: Session, trip_id: int) -> LocationLog | None:
    return (
        db.query(LocationLog)
        .filter(LocationLog.trip_id == trip_id)
        .order_by(LocationLog.timestamp.desc())
        .first()
    )
