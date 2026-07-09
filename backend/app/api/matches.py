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
from app.services.notifications import create_notification


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


@router.post("/ride-requests/{request_id}/auto-assign", response_model=MatchRead)
def auto_assign_trip_for_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_roles(UserRole.rider, UserRole.admin)),
) -> RideMatch:
    ride_request = db.get(RideRequest, request_id)
    if ride_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride request not found")
    if current_user.role != UserRole.admin and ride_request.rider_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    if ride_request.status != RideRequestStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ride request is not pending")

    recommendations = recommend_trips_for_request(db, ride_request)
    if not recommendations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No suitable driver found")
    best_match = recommendations[0]
    return confirm_match(best_match.match_id, db, current_user)


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
    match = db.query(RideMatch).filter(RideMatch.match_id == match_id).with_for_update().one_or_none()
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")

    trip = db.query(Trip).filter(Trip.trip_id == match.trip_id).with_for_update().one()
    ride_request = (
        db.query(RideRequest)
        .filter(RideRequest.request_id == match.request_id)
        .with_for_update()
        .one()
    )
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

    create_notification(
        db,
        user_id=ride_request.rider_id,
        title="Ride match confirmed",
        body=f"Your ride request #{ride_request.request_id} is confirmed for trip #{trip.trip_id}.",
        category="match",
        entity_type="match",
        entity_id=match.match_id,
    )
    create_notification(
        db,
        user_id=trip.driver_id,
        title="Passenger matched",
        body=f"Ride request #{ride_request.request_id} joined your trip #{trip.trip_id}.",
        category="match",
        entity_type="match",
        entity_id=match.match_id,
    )
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
    create_notification(
        db,
        user_id=match.rider_id,
        title="Match recommendation rejected",
        body=f"A driver rejected recommendation #{match.match_id}. You can look for another trip.",
        category="match",
        entity_type="match",
        entity_id=match.match_id,
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match
