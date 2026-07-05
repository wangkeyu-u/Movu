from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user, require_approved_roles, require_roles
from app.db.session import get_db
from app.models.enums import TripStatus, UserRole
from app.models.trip import Trip
from app.models.user import User
from app.schemas.trip import TripCreate, TripRead, TripStatusUpdate
from app.services.maps import validate_route_inside_service_area
from app.services.vehicles import get_driver_max_approved_seats


router = APIRouter(prefix="/trips", tags=["trips"])


@router.post("", response_model=TripRead, status_code=status.HTTP_201_CREATED)
def create_trip(
    payload: TripCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_roles(UserRole.driver)),
) -> Trip:
    max_approved_seats = get_driver_max_approved_seats(db, current_user.user_id)
    if max_approved_seats is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Driver must have an approved vehicle before creating trips",
        )
    if payload.available_seats > max_approved_seats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Available seats cannot exceed approved vehicle seat count",
        )
    validate_route_inside_service_area(
        origin_latitude=payload.origin_latitude,
        origin_longitude=payload.origin_longitude,
        destination_latitude=payload.destination_latitude,
        destination_longitude=payload.destination_longitude,
        require_coordinates=settings.environment == "production",
    )

    trip = Trip(
        driver_id=current_user.user_id,
        origin=payload.origin,
        destination=payload.destination,
        origin_latitude=payload.origin_latitude,
        origin_longitude=payload.origin_longitude,
        destination_latitude=payload.destination_latitude,
        destination_longitude=payload.destination_longitude,
        departure_time=payload.departure_time,
        departure_time_timezone=payload.departure_time_timezone,
        available_seats=payload.available_seats,
        total_seats=payload.available_seats,
        status=TripStatus.posted,
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


@router.get("/me", response_model=list[TripRead])
def list_my_trips(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_roles(UserRole.driver)),
) -> list[Trip]:
    return (
        db.query(Trip)
        .filter(Trip.driver_id == current_user.user_id)
        .order_by(Trip.created_at.desc())
        .all()
    )


@router.get("", response_model=list[TripRead])
def list_trips(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
    trip_status: TripStatus | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[Trip]:
    query = db.query(Trip)
    if trip_status is not None:
        query = query.filter(Trip.status == trip_status)
    return query.order_by(Trip.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{trip_id}", response_model=TripRead)
def get_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    if current_user.role != UserRole.admin and trip.driver_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    return trip


@router.patch("/{trip_id}/status", response_model=TripRead)
def update_trip_status(
    trip_id: int,
    payload: TripStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.driver)),
) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    if trip.driver_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")

    trip.status = payload.status
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip
