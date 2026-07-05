from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_approved_roles, require_roles
from app.core.config import settings
from app.db.session import get_db
from app.models.enums import RideRequestStatus, UserRole
from app.models.ride_request import RideRequest
from app.models.user import User
from app.schemas.ride_request import RideRequestCreate, RideRequestRead
from app.services.maps import calculate_route_distance_km, validate_route_inside_service_area


router = APIRouter(prefix="/ride-requests", tags=["ride requests"])


@router.post("", response_model=RideRequestRead, status_code=status.HTTP_201_CREATED)
def create_ride_request(
    payload: RideRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_roles(UserRole.rider)),
) -> RideRequest:
    coordinates_present = validate_route_inside_service_area(
        origin_latitude=payload.origin_latitude,
        origin_longitude=payload.origin_longitude,
        destination_latitude=payload.destination_latitude,
        destination_longitude=payload.destination_longitude,
        require_coordinates=settings.environment == "production",
    )
    distance_km = payload.distance_km
    if coordinates_present:
        distance_km = calculate_route_distance_km(
            origin_latitude=payload.origin_latitude,
            origin_longitude=payload.origin_longitude,
            destination_latitude=payload.destination_latitude,
            destination_longitude=payload.destination_longitude,
        )

    ride_request = RideRequest(
        rider_id=current_user.user_id,
        origin=payload.origin,
        destination=payload.destination,
        origin_latitude=payload.origin_latitude,
        origin_longitude=payload.origin_longitude,
        destination_latitude=payload.destination_latitude,
        destination_longitude=payload.destination_longitude,
        preferred_time=payload.preferred_time,
        preferred_time_timezone=payload.preferred_time_timezone,
        passenger_count=payload.passenger_count,
        gender_preference=payload.gender_preference,
        distance_km=distance_km,
        status=RideRequestStatus.pending,
    )
    db.add(ride_request)
    db.commit()
    db.refresh(ride_request)
    return ride_request


@router.get("/me", response_model=list[RideRequestRead])
def list_my_ride_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_roles(UserRole.rider)),
) -> list[RideRequest]:
    return (
        db.query(RideRequest)
        .filter(RideRequest.rider_id == current_user.user_id)
        .order_by(RideRequest.created_at.desc())
        .all()
    )


@router.get("", response_model=list[RideRequestRead])
def list_ride_requests(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
    request_status: RideRequestStatus | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[RideRequest]:
    query = db.query(RideRequest)
    if request_status is not None:
        query = query.filter(RideRequest.status == request_status)
    return query.order_by(RideRequest.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{request_id}", response_model=RideRequestRead)
def get_ride_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RideRequest:
    ride_request = db.get(RideRequest, request_id)
    if ride_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride request not found")
    if current_user.role != UserRole.admin and ride_request.rider_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    return ride_request


@router.patch("/{request_id}/cancel", response_model=RideRequestRead)
def cancel_ride_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.rider)),
) -> RideRequest:
    ride_request = db.get(RideRequest, request_id)
    if ride_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride request not found")
    if ride_request.rider_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    if ride_request.status != RideRequestStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending ride requests can be cancelled",
        )

    ride_request.status = RideRequestStatus.cancelled
    db.add(ride_request)
    db.commit()
    db.refresh(ride_request)
    return ride_request
