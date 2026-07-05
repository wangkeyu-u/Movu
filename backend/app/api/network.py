from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_approved_user
from app.db.session import get_db
from app.models.enums import MatchStatus, TripStatus, UserRole, VerificationStatus
from app.models.match import RideMatch
from app.models.ride_request import RideRequest
from app.models.trip import Trip
from app.models.trip_message import TripMessage
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.network import (
    NetworkRiderRead,
    NetworkUserRead,
    NetworkVehicleRead,
    TripMessageCreate,
    TripMessageRead,
    TripNetworkRead,
)
from app.services.location import user_can_view_trip_location


router = APIRouter(prefix="/network", tags=["network"])

NETWORK_TRIP_STATUSES = {TripStatus.matched, TripStatus.ongoing, TripStatus.completed}


def _trip_or_404(db: Session, trip_id: int) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return trip


def _message_read(message: TripMessage) -> TripMessageRead:
    return TripMessageRead(
        message_id=message.message_id,
        trip_id=message.trip_id,
        sender_id=message.sender_id,
        sender_name=message.sender.name,
        sender_role=message.sender.role.value,
        body=message.body,
        created_at=message.created_at,
    )


def _network_trip_read(db: Session, trip: Trip) -> TripNetworkRead:
    vehicle = (
        db.query(Vehicle)
        .filter(
            Vehicle.driver_id == trip.driver_id,
            Vehicle.verification_status == VerificationStatus.approved,
        )
        .order_by(Vehicle.created_at.desc())
        .first()
    )
    rider_rows = (
        db.query(User, RideRequest)
        .join(RideMatch, RideMatch.rider_id == User.user_id)
        .join(RideRequest, RideRequest.request_id == RideMatch.request_id)
        .filter(RideMatch.trip_id == trip.trip_id, RideMatch.status == MatchStatus.confirmed)
        .order_by(RideMatch.created_at.asc())
        .all()
    )
    return TripNetworkRead(
        trip_id=trip.trip_id,
        driver_id=trip.driver_id,
        origin=trip.origin,
        destination=trip.destination,
        origin_latitude=trip.origin_latitude,
        origin_longitude=trip.origin_longitude,
        destination_latitude=trip.destination_latitude,
        destination_longitude=trip.destination_longitude,
        departure_time=trip.departure_time,
        departure_time_timezone=trip.departure_time_timezone,
        available_seats=trip.available_seats,
        total_seats=trip.total_seats,
        status=trip.status,
        created_at=trip.created_at,
        driver=NetworkUserRead(
            user_id=trip.driver.user_id,
            name=trip.driver.name,
            role=trip.driver.role.value,
            rating=trip.driver.rating,
        ),
        vehicle=NetworkVehicleRead(
            vehicle_id=vehicle.vehicle_id,
            plate_number=vehicle.plate_number,
            vehicle_model=vehicle.vehicle_model,
            seat_count=vehicle.seat_count,
            verification_status=vehicle.verification_status,
        ) if vehicle is not None else None,
        riders=[
            NetworkRiderRead(
                user_id=rider.user_id,
                name=rider.name,
                rating=rider.rating,
                passenger_count=ride_request.passenger_count,
                pickup=ride_request.origin,
                dropoff=ride_request.destination,
            )
            for rider, ride_request in rider_rows
        ],
    )


@router.get("/me/trips", response_model=list[TripNetworkRead])
def list_my_network_trips(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> list[TripNetworkRead]:
    if current_user.role == UserRole.driver:
        trips = (
            db.query(Trip)
            .filter(Trip.driver_id == current_user.user_id, Trip.status.in_(NETWORK_TRIP_STATUSES))
            .order_by(Trip.departure_time.desc())
            .all()
        )
        return [_network_trip_read(db, trip) for trip in trips]
    if current_user.role == UserRole.rider:
        trips = (
            db.query(Trip)
            .join(RideMatch, RideMatch.trip_id == Trip.trip_id)
            .filter(
                RideMatch.rider_id == current_user.user_id,
                RideMatch.status == MatchStatus.confirmed,
                Trip.status.in_(NETWORK_TRIP_STATUSES),
            )
            .order_by(Trip.departure_time.desc())
            .all()
        )
        return [_network_trip_read(db, trip) for trip in trips]
    return []


@router.get("/trips/{trip_id}/messages", response_model=list[TripMessageRead])
def list_trip_messages(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[TripMessageRead]:
    trip = _trip_or_404(db, trip_id)
    if not user_can_view_trip_location(db, current_user, trip):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    messages = (
        db.query(TripMessage)
        .filter(TripMessage.trip_id == trip_id)
        .order_by(TripMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return [_message_read(message) for message in reversed(messages)]


@router.post("/trips/{trip_id}/messages", response_model=TripMessageRead, status_code=status.HTTP_201_CREATED)
def create_trip_message(
    trip_id: int,
    payload: TripMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> TripMessageRead:
    trip = _trip_or_404(db, trip_id)
    if not user_can_view_trip_location(db, current_user, trip):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    message = TripMessage(trip_id=trip_id, sender_id=current_user.user_id, body=payload.body.strip())
    db.add(message)
    db.commit()
    db.refresh(message)
    return _message_read(message)
