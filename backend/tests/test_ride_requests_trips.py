from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.enums import Gender, RideRequestStatus, UserRole, VerificationStatus
from app.models.ride_request import RideRequest
from app.models.vehicle import Vehicle
from app.core.config import settings
from tests.conftest import auth_headers_for, create_admin_user, create_user


def future_time(hours: int = 2) -> str:
    return (datetime.now(UTC) + timedelta(hours=hours)).isoformat()


def ride_request_payload() -> dict[str, str | int | float]:
    return {
        "origin": "Taylor's Lakeside Campus",
        "destination": "Sunway Pyramid",
        "preferred_time": future_time(),
        "passenger_count": 2,
        "gender_preference": "same_gender",
        "distance_km": 5.2,
    }


def ride_request_payload_with_coordinates() -> dict[str, str | int | float]:
    payload = ride_request_payload()
    payload.update(
        {
            "origin_latitude": 3.0621,
            "origin_longitude": 101.6167,
            "destination_latitude": 3.0738,
            "destination_longitude": 101.6070,
            "distance_km": 999,
        }
    )
    return payload


def trip_payload(available_seats: int = 4) -> dict[str, str | int]:
    return {
        "origin": "Taylor's Lakeside Campus",
        "destination": "KL Sentral",
        "departure_time": future_time(),
        "available_seats": available_seats,
    }


def trip_payload_with_coordinates(available_seats: int = 4) -> dict[str, str | int | float]:
    payload = trip_payload(available_seats)
    payload.update(
        {
            "origin_latitude": 3.0646,
            "origin_longitude": 101.6159,
            "destination_latitude": 3.0738,
            "destination_longitude": 101.6070,
        }
    )
    return payload


def create_rider(db_session: Session):
    return create_user(
        db_session,
        name="Aina Tan",
        email="rider-step4@sd.taylors.edu.my",
        role=UserRole.rider,
        gender=Gender.female,
        student_id="R4001",
    )


def create_driver(db_session: Session, email: str = "driver-step4@sd.taylors.edu.my"):
    return create_user(
        db_session,
        name="Daniel Lim",
        email=email,
        role=UserRole.driver,
        gender=Gender.male,
        student_id=email.split("@")[0],
    )


def create_approved_vehicle(db_session: Session, driver_id: int, seat_count: int = 4) -> Vehicle:
    vehicle = Vehicle(
        driver_id=driver_id,
        plate_number=f"APP{driver_id}",
        vehicle_model="Perodua Myvi",
        seat_count=seat_count,
        verification_status=VerificationStatus.approved,
    )
    db_session.add(vehicle)
    db_session.commit()
    db_session.refresh(vehicle)
    return vehicle


def test_rider_can_create_and_cancel_ride_request(client, db_session: Session):
    rider = create_rider(db_session)

    create_response = client.post(
        "/api/ride-requests",
        json=ride_request_payload(),
        headers=auth_headers_for(rider),
    )
    request_id = create_response.json()["request_id"]
    cancel_response = client.patch(
        f"/api/ride-requests/{request_id}/cancel",
        headers=auth_headers_for(rider),
    )

    assert create_response.status_code == 201
    assert create_response.json()["status"] == "pending"
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"


def test_ride_request_with_coordinates_uses_route_distance(
    client,
    db_session: Session,
    monkeypatch,
):
    rider = create_rider(db_session)
    monkeypatch.setattr(
        "app.api.ride_requests.calculate_route_distance_km",
        lambda **_: 6.4,
    )

    response = client.post(
        "/api/ride-requests",
        json=ride_request_payload_with_coordinates(),
        headers=auth_headers_for(rider),
    )

    assert response.status_code == 201
    assert response.json()["distance_km"] == 6.4


def test_ride_request_rejects_coordinates_outside_taylors_service_area(client, db_session: Session):
    rider = create_rider(db_session)
    payload = ride_request_payload_with_coordinates()
    payload["destination_latitude"] = 3.4470
    payload["destination_longitude"] = 101.7930

    response = client.post(
        "/api/ride-requests",
        json=payload,
        headers=auth_headers_for(rider),
    )

    assert response.status_code == 400
    assert "service area" in response.json()["detail"]


def test_ride_request_rejects_partial_coordinates(client, db_session: Session):
    rider = create_rider(db_session)
    payload = ride_request_payload()
    payload["origin_latitude"] = 3.0646

    response = client.post(
        "/api/ride-requests",
        json=payload,
        headers=auth_headers_for(rider),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Origin and destination coordinates are required"


def test_driver_cannot_create_ride_request(client, db_session: Session):
    driver = create_driver(db_session)

    response = client.post(
        "/api/ride-requests",
        json=ride_request_payload(),
        headers=auth_headers_for(driver),
    )

    assert response.status_code == 403


def test_rider_cannot_cancel_another_riders_request(client, db_session: Session):
    owner = create_rider(db_session)
    other = create_user(
        db_session,
        name="Other Rider",
        email="other-rider-step4@sd.taylors.edu.my",
        role=UserRole.rider,
        gender=Gender.female,
        student_id="R4002",
    )
    create_response = client.post(
        "/api/ride-requests",
        json=ride_request_payload(),
        headers=auth_headers_for(owner),
    )
    request_id = create_response.json()["request_id"]

    response = client.patch(
        f"/api/ride-requests/{request_id}/cancel",
        headers=auth_headers_for(other),
    )

    assert response.status_code == 403


def test_driver_cannot_directly_cancel_rider_request(client, db_session: Session):
    rider = create_rider(db_session)
    driver = create_driver(db_session)
    create_response = client.post(
        "/api/ride-requests",
        json=ride_request_payload(),
        headers=auth_headers_for(rider),
    )
    request_id = create_response.json()["request_id"]

    response = client.patch(
        f"/api/ride-requests/{request_id}/cancel",
        headers=auth_headers_for(driver),
    )

    assert response.status_code == 403


def test_pending_rider_cannot_create_ride_request(client, db_session: Session):
    rider = create_user(
        db_session,
        name="Pending Rider",
        email="pending-rider@sd.taylors.edu.my",
        role=UserRole.rider,
        gender=Gender.female,
        student_id="PEND-R",
        verification_status=VerificationStatus.pending,
        email_verified=True,
    )

    response = client.post(
        "/api/ride-requests",
        json=ride_request_payload(),
        headers=auth_headers_for(rider),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Account is not approved"


def test_cannot_cancel_non_pending_ride_request(client, db_session: Session):
    rider = create_rider(db_session)
    ride_request = RideRequest(
        rider_id=rider.user_id,
        origin="Taylor's Lakeside Campus",
        destination="Sunway Pyramid",
        preferred_time=datetime.now(UTC) + timedelta(hours=2),
        passenger_count=1,
        status=RideRequestStatus.matched,
    )
    db_session.add(ride_request)
    db_session.commit()
    db_session.refresh(ride_request)

    response = client.patch(
        f"/api/ride-requests/{ride_request.request_id}/cancel",
        headers=auth_headers_for(rider),
    )

    assert response.status_code == 400


def test_admin_can_list_ride_requests(client, db_session: Session):
    admin = create_admin_user(db_session)
    rider = create_rider(db_session)
    client.post(
        "/api/ride-requests",
        json=ride_request_payload(),
        headers=auth_headers_for(rider),
    )

    response = client.get("/api/ride-requests", headers=auth_headers_for(admin))

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_driver_without_approved_vehicle_cannot_create_trip(client, db_session: Session):
    driver = create_driver(db_session)

    response = client.post("/api/trips", json=trip_payload(), headers=auth_headers_for(driver))

    assert response.status_code == 403


def test_driver_with_approved_vehicle_can_create_trip(client, db_session: Session):
    driver = create_driver(db_session)
    create_approved_vehicle(db_session, driver.user_id)

    response = client.post("/api/trips", json=trip_payload(), headers=auth_headers_for(driver))

    assert response.status_code == 201
    body = response.json()
    assert body["driver_id"] == driver.user_id
    assert body["available_seats"] == 4
    assert body["total_seats"] == 4
    assert body["status"] == "posted"


def test_driver_can_create_trip_with_coordinates_inside_service_area(client, db_session: Session):
    driver = create_driver(db_session)
    create_approved_vehicle(db_session, driver.user_id)

    response = client.post(
        "/api/trips",
        json=trip_payload_with_coordinates(),
        headers=auth_headers_for(driver),
    )

    assert response.status_code == 201
    assert response.json()["origin_latitude"] == 3.0646


def test_trip_rejects_coordinates_outside_taylors_service_area(client, db_session: Session):
    driver = create_driver(db_session)
    create_approved_vehicle(db_session, driver.user_id)
    payload = trip_payload_with_coordinates()
    payload["destination_latitude"] = 3.4470
    payload["destination_longitude"] = 101.7930

    response = client.post("/api/trips", json=payload, headers=auth_headers_for(driver))

    assert response.status_code == 400
    assert "service area" in response.json()["detail"]


def test_production_trip_requires_coordinates(client, db_session: Session, monkeypatch):
    driver = create_driver(db_session)
    create_approved_vehicle(db_session, driver.user_id)
    monkeypatch.setattr(settings, "environment", "production")

    response = client.post("/api/trips", json=trip_payload(), headers=auth_headers_for(driver))

    assert response.status_code == 400
    assert response.json()["detail"] == "Origin and destination coordinates are required"


def test_trip_seats_cannot_exceed_approved_vehicle(client, db_session: Session):
    driver = create_driver(db_session)
    create_approved_vehicle(db_session, driver.user_id, seat_count=3)

    response = client.post("/api/trips", json=trip_payload(available_seats=4), headers=auth_headers_for(driver))

    assert response.status_code == 400


def test_driver_can_update_own_trip_status(client, db_session: Session):
    driver = create_driver(db_session)
    create_approved_vehicle(db_session, driver.user_id)
    create_response = client.post("/api/trips", json=trip_payload(), headers=auth_headers_for(driver))
    trip_id = create_response.json()["trip_id"]

    update_response = client.patch(
        f"/api/trips/{trip_id}/status",
        json={"status": "ongoing"},
        headers=auth_headers_for(driver),
    )

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "ongoing"


def test_rider_cannot_update_trip_status(client, db_session: Session):
    driver = create_driver(db_session)
    rider = create_rider(db_session)
    create_approved_vehicle(db_session, driver.user_id)
    create_response = client.post("/api/trips", json=trip_payload(), headers=auth_headers_for(driver))
    trip_id = create_response.json()["trip_id"]

    update_response = client.patch(
        f"/api/trips/{trip_id}/status",
        json={"status": "ongoing"},
        headers=auth_headers_for(rider),
    )

    assert update_response.status_code == 403


def test_other_driver_cannot_update_trip_status(client, db_session: Session):
    owner = create_driver(db_session, email="owner@sd.taylors.edu.my")
    other = create_driver(db_session, email="other@sd.taylors.edu.my")
    create_approved_vehicle(db_session, owner.user_id)
    create_response = client.post("/api/trips", json=trip_payload(), headers=auth_headers_for(owner))
    trip_id = create_response.json()["trip_id"]

    update_response = client.patch(
        f"/api/trips/{trip_id}/status",
        json={"status": "ongoing"},
        headers=auth_headers_for(other),
    )

    assert update_response.status_code == 403


def test_admin_can_list_trips(client, db_session: Session):
    admin = create_admin_user(db_session)
    driver = create_driver(db_session)
    create_approved_vehicle(db_session, driver.user_id)
    client.post("/api/trips", json=trip_payload(), headers=auth_headers_for(driver))

    response = client.get("/api/trips", headers=auth_headers_for(admin))

    assert response.status_code == 200
    assert len(response.json()) == 1
