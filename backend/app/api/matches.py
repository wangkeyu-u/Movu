from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_approved_roles, require_approved_user, require_roles
from app.db.session import get_db
from app.models.enums import MatchStatus, RideRequestStatus, TripStatus, UserRole
from app.models.match import RideMatch
from app.models.ride_request import RideRequest
from app.models.trip import Trip
from app.models.user import User
from app.schemas.match import MatchRead
from app.services.matching import recommend_requests_for_trip, recommend_trips_for_request


router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=list[MatchRead])
def list_matches(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
    match_status: MatchStatus | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[RideMatch]:
    query = db.query(RideMatch)
    if match_status is not None:
        query = query.filter(RideMatch.status == match_status)
    return query.order_by(RideMatch.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/ride-requests/{request_id}/recommendations", response_model=list[MatchRead])
def get_trip_recommendations(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> list[RideMatch]:
    ride_request = db.get(RideRequest, request_id)
    if ride_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride request not found")
    if current_user.role != UserRole.admin and ride_request.rider_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    if ride_request.status != RideRequestStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending ride requests can receive recommendations",
        )
    return recommend_trips_for_request(db, ride_request)


@router.get("/trips/{trip_id}/recommendations", response_model=list[MatchRead])
def get_request_recommendations(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> list[RideMatch]:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    if current_user.role != UserRole.admin and trip.driver_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    if trip.status not in {TripStatus.posted, TripStatus.matched}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only posted or matched trips can receive recommendations",
        )
    return recommend_requests_for_trip(db, trip)


@router.post("/{match_id}/confirm", response_model=MatchRead)
def confirm_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> RideMatch:
    match = db.get(RideMatch, match_id)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")

    trip = match.trip
    ride_request = match.ride_request
    is_rider = current_user.user_id == ride_request.rider_id
    is_driver = current_user.user_id == trip.driver_id
    if current_user.role != UserRole.admin and not (is_rider or is_driver):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    if match.status not in {MatchStatus.recommended, MatchStatus.confirmed}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Match cannot be confirmed")
    if ride_request.status != RideRequestStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ride request is not pending")
    if trip.status not in {TripStatus.posted, TripStatus.matched}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trip is not available")
    if trip.available_seats < ride_request.passenger_count:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trip does not have enough seats")

    match.status = MatchStatus.confirmed
    ride_request.status = RideRequestStatus.matched
    trip.available_seats -= ride_request.passenger_count
    trip.status = TripStatus.full if trip.available_seats == 0 else TripStatus.matched

    other_matches = (
        db.query(RideMatch)
        .filter(
            RideMatch.request_id == ride_request.request_id,
            RideMatch.match_id != match.match_id,
            RideMatch.status == MatchStatus.recommended,
        )
        .all()
    )
    for other_match in other_matches:
        other_match.status = MatchStatus.cancelled
        db.add(other_match)

    db.add_all([match, ride_request, trip])
    db.commit()
    db.refresh(match)
    return match


@router.post("/{match_id}/reject", response_model=MatchRead)
def reject_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_roles(UserRole.driver, UserRole.admin)),
) -> RideMatch:
    match = db.get(RideMatch, match_id)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    if current_user.role != UserRole.admin and match.trip.driver_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    if match.status == MatchStatus.confirmed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Confirmed matches cannot be rejected")

    match.status = MatchStatus.rejected
    db.add(match)
    db.commit()
    db.refresh(match)
    return match
