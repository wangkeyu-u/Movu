from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_approved_roles, require_roles
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import UserRole, VerificationStatus
from app.models.location_log import LocationLog
from app.models.trip import Trip
from app.models.user import User
from app.schemas.location import LocationCreate, LocationMessage, LocationRead
from app.services.location import (
    get_latest_trip_location,
    record_driver_location,
    user_can_view_trip_location,
)
from app.services.realtime import location_manager


router = APIRouter(prefix="/locations", tags=["locations"])
ws_router = APIRouter(tags=["location websocket"])


def _get_trip_or_404(db: Session, trip_id: int) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return trip


def _authenticate_ws_user(token: str | None, db: Session) -> User | None:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
    except ValueError:
        return None
    email = payload.get("sub")
    if not isinstance(email, str):
        return None
    user = db.query(User).filter(User.email == email).first()
    if user is None or user.is_banned:
        return None
    if user.role != UserRole.admin and (
        not user.email_verified or user.verification_status != VerificationStatus.approved
    ):
        return None
    return user


@router.post("", response_model=LocationRead, status_code=status.HTTP_201_CREATED)
async def create_location_log(
    payload: LocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_roles(UserRole.driver)),
) -> LocationLog:
    trip = _get_trip_or_404(db, payload.trip_id)
    log = record_driver_location(
        db,
        trip=trip,
        user=current_user,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    await location_manager.broadcast_trip_location(
        trip.trip_id,
        LocationMessage(
            trip_id=log.trip_id,
            user_id=log.user_id,
            latitude=log.latitude,
            longitude=log.longitude,
            timestamp=log.timestamp,
        ).model_dump(mode="json"),
    )
    return log


@router.get("/trips/{trip_id}/latest", response_model=LocationRead)
def read_latest_trip_location(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LocationLog:
    trip = _get_trip_or_404(db, trip_id)
    if not user_can_view_trip_location(db, current_user, trip):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    latest = get_latest_trip_location(db, trip_id)
    if latest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No location found")
    return latest


@router.get("/trips/{trip_id}/logs", response_model=list[LocationRead])
def list_trip_location_logs(
    trip_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[LocationLog]:
    _get_trip_or_404(db, trip_id)
    return (
        db.query(LocationLog)
        .filter(LocationLog.trip_id == trip_id)
        .order_by(LocationLog.timestamp.desc())
        .limit(limit)
        .all()
    )


@ws_router.websocket("/ws/locations/{trip_id}")
async def websocket_trip_location(
    websocket: WebSocket,
    trip_id: int,
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> None:
    user = _authenticate_ws_user(token, db)
    trip = db.get(Trip, trip_id)
    if user is None or trip is None or not user_can_view_trip_location(db, user, trip):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await location_manager.connect(trip_id, websocket)
    try:
        while True:
            payload = await websocket.receive_json()
            latitude = float(payload["latitude"])
            longitude = float(payload["longitude"])
            log = record_driver_location(
                db,
                trip=trip,
                user=user,
                latitude=latitude,
                longitude=longitude,
            )
            await location_manager.broadcast_trip_location(
                trip_id,
                LocationMessage(
                    trip_id=log.trip_id,
                    user_id=log.user_id,
                    latitude=log.latitude,
                    longitude=log.longitude,
                    timestamp=log.timestamp,
                ).model_dump(mode="json"),
            )
    except (WebSocketDisconnect, HTTPException, KeyError, TypeError, ValueError):
        location_manager.disconnect(trip_id, websocket)
