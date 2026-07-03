from sqlalchemy.orm import Session

from app.models.enums import Gender, UserRole, VerificationStatus
from app.models.audit_log import AuditLog
from app.models.vehicle import Vehicle
from tests.conftest import auth_headers_for, create_admin_user, create_user


def vehicle_payload(plate_number: str = "VBN 1234") -> dict[str, str | int]:
    return {
        "plate_number": plate_number,
        "vehicle_model": "Perodua Myvi",
        "seat_count": 4,
    }


def create_driver(db_session: Session):
    return create_user(
        db_session,
        name="Daniel Lim",
        email="driver1@sd.taylors.edu.my",
        role=UserRole.driver,
        gender=Gender.male,
        student_id="D1001",
    )


def test_driver_can_register_vehicle(client, db_session: Session):
    driver = create_driver(db_session)

    response = client.post(
        "/api/vehicles",
        json=vehicle_payload(),
        headers=auth_headers_for(driver),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["driver_id"] == driver.user_id
    assert body["plate_number"] == "VBN1234"
    assert body["verification_status"] == "pending"


def test_rider_cannot_register_vehicle(client, db_session: Session):
    rider = create_user(
        db_session,
        name="Aina Tan",
        email="rider2@sd.taylors.edu.my",
        role=UserRole.rider,
        gender=Gender.female,
        student_id="R2002",
    )

    response = client.post(
        "/api/vehicles",
        json=vehicle_payload(),
        headers=auth_headers_for(rider),
    )

    assert response.status_code == 403


def test_pending_driver_cannot_register_vehicle(client, db_session: Session):
    driver = create_user(
        db_session,
        name="Pending Driver",
        email="pending-driver@sd.taylors.edu.my",
        role=UserRole.driver,
        gender=Gender.male,
        student_id="PEND-D",
        verification_status=VerificationStatus.pending,
        email_verified=True,
    )

    response = client.post(
        "/api/vehicles",
        json=vehicle_payload(),
        headers=auth_headers_for(driver),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Account is not approved"


def test_admin_can_approve_vehicle(client, db_session: Session):
    admin = create_admin_user(db_session)
    driver = create_driver(db_session)
    vehicle = Vehicle(
        driver_id=driver.user_id,
        plate_number="ABC1234",
        vehicle_model="Honda City",
        seat_count=4,
    )
    db_session.add(vehicle)
    db_session.commit()
    db_session.refresh(vehicle)

    response = client.patch(
        f"/api/vehicles/{vehicle.vehicle_id}/verification",
        json={"verification_status": "approved"},
        headers=auth_headers_for(admin),
    )

    assert response.status_code == 200
    assert response.json()["verification_status"] == "approved"
    audit_log = db_session.query(AuditLog).filter(AuditLog.action == "vehicle.verification_updated").one()
    assert audit_log.entity_type == "vehicle"
    assert audit_log.entity_id == str(vehicle.vehicle_id)


def test_non_admin_cannot_approve_vehicle(client, db_session: Session):
    driver = create_driver(db_session)
    vehicle = Vehicle(
        driver_id=driver.user_id,
        plate_number="ABC1234",
        vehicle_model="Honda City",
        seat_count=4,
    )
    db_session.add(vehicle)
    db_session.commit()
    db_session.refresh(vehicle)

    response = client.patch(
        f"/api/vehicles/{vehicle.vehicle_id}/verification",
        json={"verification_status": "approved"},
        headers=auth_headers_for(driver),
    )

    assert response.status_code == 403


def test_duplicate_plate_number_is_rejected(client, db_session: Session):
    driver = create_driver(db_session)
    headers = auth_headers_for(driver)

    first_response = client.post("/api/vehicles", json=vehicle_payload(), headers=headers)
    duplicate_response = client.post(
        "/api/vehicles",
        json=vehicle_payload(plate_number="VBN1234"),
        headers=headers,
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
