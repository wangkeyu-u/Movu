from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_approved_roles, require_roles
from app.db.session import get_db
from app.models.enums import UserRole, VerificationStatus
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleRead, VehicleVerificationUpdate
from app.services.audit import write_audit_log
from app.services.notifications import create_notification, notify_admins


router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.post("", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
def register_vehicle(
    payload: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_roles(UserRole.driver)),
) -> Vehicle:
    existing_vehicle = (
        db.query(Vehicle).filter(Vehicle.plate_number == payload.plate_number).first()
    )
    if existing_vehicle is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Plate number already exists")

    vehicle = Vehicle(
        driver_id=current_user.user_id,
        plate_number=payload.plate_number,
        vehicle_model=payload.vehicle_model,
        seat_count=payload.seat_count,
        verification_status=VerificationStatus.pending,
    )
    db.add(vehicle)
    db.flush()
    notify_admins(
        db,
        title="Vehicle needs review",
        body=f"{current_user.name} submitted {payload.plate_number} for approval.",
        category="verification",
        entity_type="vehicle",
        entity_id=vehicle.vehicle_id,
    )
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.get("/me", response_model=list[VehicleRead])
def list_my_vehicles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.driver)),
) -> list[Vehicle]:
    return (
        db.query(Vehicle)
        .filter(Vehicle.driver_id == current_user.user_id)
        .order_by(Vehicle.created_at.desc())
        .all()
    )


@router.get("", response_model=list[VehicleRead])
def list_vehicles(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
    verification_status: VerificationStatus | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[Vehicle]:
    query = db.query(Vehicle)
    if verification_status is not None:
        query = query.filter(Vehicle.verification_status == verification_status)
    return query.order_by(Vehicle.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{vehicle_id}", response_model=VehicleRead)
def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Vehicle:
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    if current_user.role != UserRole.admin and vehicle.driver_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    return vehicle


@router.patch("/{vehicle_id}/verification", response_model=VehicleRead)
def update_vehicle_verification(
    vehicle_id: int,
    payload: VehicleVerificationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles(UserRole.admin)),
) -> Vehicle:
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    vehicle.verification_status = payload.verification_status
    write_audit_log(
        db,
        actor=admin_user,
        action="vehicle.verification_updated",
        entity_type="vehicle",
        entity_id=vehicle.vehicle_id,
        request=request,
        metadata={"verification_status": payload.verification_status.value},
    )
    create_notification(
        db,
        user_id=vehicle.driver_id,
        title="Vehicle review updated",
        body=f"Your vehicle {vehicle.plate_number} is now {payload.verification_status.value}.",
        category="verification",
        entity_type="vehicle",
        entity_id=vehicle.vehicle_id,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle
