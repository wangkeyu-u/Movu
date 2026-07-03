from sqlalchemy.orm import Session

from app.models.enums import VerificationStatus
from app.models.vehicle import Vehicle


def driver_has_approved_vehicle(db: Session, driver_id: int) -> bool:
    return (
        db.query(Vehicle)
        .filter(
            Vehicle.driver_id == driver_id,
            Vehicle.verification_status == VerificationStatus.approved,
        )
        .first()
        is not None
    )


def get_driver_max_approved_seats(db: Session, driver_id: int) -> int | None:
    vehicles = (
        db.query(Vehicle)
        .filter(
            Vehicle.driver_id == driver_id,
            Vehicle.verification_status == VerificationStatus.approved,
        )
        .all()
    )
    if not vehicles:
        return None
    return max(vehicle.seat_count for vehicle in vehicles)
