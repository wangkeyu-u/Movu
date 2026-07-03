from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import MatchStatus, TripStatus
from app.models.match import RideMatch
from app.models.rating_report import RatingReport
from app.models.trip import Trip
from app.models.user import User


def assert_trip_completed_and_participants(
    db: Session,
    *,
    from_user: User,
    to_user_id: int,
    trip_id: int,
) -> Trip:
    if from_user.user_id == to_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot rate or report yourself")

    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    if trip.status != TripStatus.completed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trip must be completed")

    confirmed_matches = (
        db.query(RideMatch)
        .filter(RideMatch.trip_id == trip_id, RideMatch.status == MatchStatus.confirmed)
        .all()
    )
    participant_ids = {trip.driver_id}
    participant_ids.update(match.rider_id for match in confirmed_matches)
    if from_user.user_id not in participant_ids or to_user_id not in participant_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Users are not trip participants")
    return trip


def recalculate_user_rating(db: Session, user_id: int) -> float:
    rating_records = (
        db.query(RatingReport)
        .filter(RatingReport.to_user_id == user_id, RatingReport.score.isnot(None))
        .all()
    )
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not rating_records:
        user.rating = 5.0
    else:
        user.rating = round(
            sum(record.score for record in rating_records if record.score is not None) / len(rating_records),
            2,
        )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.rating
