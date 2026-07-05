from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_approved_user, require_roles
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import MatchStatus, SOSStatus, TripStatus, UserRole
from app.models.match import RideMatch
from app.models.sos_event import SOSEvent
from app.models.trip import Trip
from app.models.user import User
from app.models.time import utc_now
from app.schemas.sos import SOSCreate, SOSRead, SOSStatusUpdate
from app.schemas.trip import TripRead
from app.services.location import user_can_view_trip_location
from app.services.realtime import sos_alert_manager
from app.services.audit import write_audit_log


router = APIRouter(prefix="/sos", tags=["sos"])
ws_router = APIRouter(tags=["sos websocket"])

SAFETY_TRIP_STATUSES = {TripStatus.ongoing, TripStatus.matched, TripStatus.completed}


def _safety_trip_rank(trip: Trip) -> tuple[int, object]:
    status_rank = {
        TripStatus.ongoing: 0,
        TripStatus.matched: 1,
        TripStatus.completed: 2,
    }.get(trip.status, 9)
    return status_rank, -trip.departure_time.timestamp()


def _current_safety_trip(db: Session, user: User) -> Trip | None:
    if user.role == UserRole.driver:
        trips = (
            db.query(Trip)
            .filter(Trip.driver_id == user.user_id, Trip.status.in_(SAFETY_TRIP_STATUSES))
            .all()
        )
    elif user.role == UserRole.rider:
        trips = (
            db.query(Trip)
            .join(RideMatch, RideMatch.trip_id == Trip.trip_id)
            .filter(
                RideMatch.rider_id == user.user_id,
                RideMatch.status == MatchStatus.confirmed,
                Trip.status.in_(SAFETY_TRIP_STATUSES),
            )
            .all()
        )
    else:
        trips = []
    if not trips:
        return None
    return sorted(trips, key=_safety_trip_rank)[0]


def _authenticate_ws_admin(token: str | None, db: Session) -> User | None:
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
    if user is None or user.role != UserRole.admin or user.is_banned:
        return None
    return user


@router.post("", response_model=SOSRead, status_code=status.HTTP_201_CREATED)
async def create_sos_event(
    payload: SOSCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> SOSEvent:
    trip = db.get(Trip, payload.trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    if trip.status not in SAFETY_TRIP_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active or recent trip found")
    if not user_can_view_trip_location(db, current_user, trip):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")

    sos_event = SOSEvent(
        user_id=current_user.user_id,
        trip_id=payload.trip_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        status=SOSStatus.new,
    )
    db.add(sos_event)
    db.commit()
    db.refresh(sos_event)

    await sos_alert_manager.broadcast(SOSRead.model_validate(sos_event).model_dump(mode="json"))
    return sos_event


@router.get("/current-trip", response_model=TripRead)
def read_current_safety_trip(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> Trip:
    trip = _current_safety_trip(db, current_user)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active or recent trip found")
    return trip


@router.get("/me", response_model=list[SOSRead])
def list_my_sos_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SOSEvent]:
    return (
        db.query(SOSEvent)
        .filter(SOSEvent.user_id == current_user.user_id)
        .order_by(SOSEvent.triggered_time.desc())
        .all()
    )


@router.get("", response_model=list[SOSRead])
def list_sos_events(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
    sos_status: SOSStatus | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[SOSEvent]:
    query = db.query(SOSEvent)
    if sos_status is not None:
        query = query.filter(SOSEvent.status == sos_status)
    return query.order_by(SOSEvent.triggered_time.desc()).offset(skip).limit(limit).all()


@router.patch("/{sos_id}/status", response_model=SOSRead)
def update_sos_status(
    sos_id: int,
    payload: SOSStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles(UserRole.admin)),
) -> SOSEvent:
    sos_event = db.get(SOSEvent, sos_id)
    if sos_event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOS event not found")

    sos_event.status = payload.status
    if payload.status in {SOSStatus.resolved, SOSStatus.false_alarm}:
        sos_event.resolved_time = utc_now()
    write_audit_log(
        db,
        actor=admin_user,
        action="sos.status_updated",
        entity_type="sos_event",
        entity_id=sos_event.sos_id,
        request=request,
        metadata={"status": payload.status.value},
    )
    db.add(sos_event)
    db.commit()
    db.refresh(sos_event)
    return sos_event


@ws_router.websocket("/ws/admin/sos")
async def websocket_admin_sos_alerts(
    websocket: WebSocket,
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> None:
    user = _authenticate_ws_admin(token, db)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await sos_alert_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        sos_alert_manager.disconnect(websocket)
