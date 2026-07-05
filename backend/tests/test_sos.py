from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.enums import Gender, MatchStatus, RideRequestStatus, TripStatus, UserRole
from app.models.match import RideMatch
from app.models.ride_request import RideRequest
from app.models.trip import Trip
from tests.conftest import auth_headers_for, create_admin_user, create_user


def bearer_token(user) -> str:
    return auth_headers_for(user)["Authorization"].split(" ", 1)[1]


def create_trip_with_confirmed_rider(db_session: Session):
    driver = create_user(
        db_session,
        name="SOS Driver",
        email="sos-driver@sd.taylors.edu.my",
        role=UserRole.driver,
        gender=Gender.male,
        student_id="SOS-D",
    )
    rider = create_user(
        db_session,
        name="SOS Rider",
        email="sos-rider@sd.taylors.edu.my",
        role=UserRole.rider,
        gender=Gender.female,
        student_id="SOS-R",
    )
    trip = Trip(
        driver_id=driver.user_id,
        origin="Taylor's Lakeside Campus",
        destination="KL Sentral",
        departure_time=datetime.now(UTC) + timedelta(minutes=5),
        available_seats=2,
        total_seats=4,
        status=TripStatus.ongoing,
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)
    ride_request = RideRequest(
        rider_id=rider.user_id,
        origin=trip.origin,
        destination=trip.destination,
        preferred_time=trip.departure_time,
        passenger_count=1,
        status=RideRequestStatus.matched,
    )
    db_session.add(ride_request)
    db_session.commit()
    db_session.refresh(ride_request)
    match = RideMatch(
        trip_id=trip.trip_id,
        request_id=ride_request.request_id,
        rider_id=rider.user_id,
        match_score=90,
        status=MatchStatus.confirmed,
    )
    db_session.add(match)
    db_session.commit()
    return driver, rider, trip


def sos_payload(trip_id: int) -> dict[str, int | float]:
    return {"trip_id": trip_id, "latitude": 3.0621, "longitude": 101.6167}


def test_confirmed_rider_can_create_sos_event(client, db_session: Session):
    _, rider, trip = create_trip_with_confirmed_rider(db_session)

    response = client.post("/api/sos", json=sos_payload(trip.trip_id), headers=auth_headers_for(rider))

    assert response.status_code == 201
    assert response.json()["status"] == "new"
    assert response.json()["user_id"] == rider.user_id


def test_trip_driver_can_create_sos_event(client, db_session: Session):
    driver, _, trip = create_trip_with_confirmed_rider(db_session)

    response = client.post("/api/sos", json=sos_payload(trip.trip_id), headers=auth_headers_for(driver))

    assert response.status_code == 201
    assert response.json()["status"] == "new"
    assert response.json()["user_id"] == driver.user_id


def test_current_safety_trip_is_inferred_for_rider_and_driver(client, db_session: Session):
    driver, rider, trip = create_trip_with_confirmed_rider(db_session)

    rider_response = client.get("/api/sos/current-trip", headers=auth_headers_for(rider))
    driver_response = client.get("/api/sos/current-trip", headers=auth_headers_for(driver))

    assert rider_response.status_code == 200
    assert driver_response.status_code == 200
    assert rider_response.json()["trip_id"] == trip.trip_id
    assert driver_response.json()["trip_id"] == trip.trip_id


def test_unrelated_user_cannot_create_sos_event(client, db_session: Session):
    _, _, trip = create_trip_with_confirmed_rider(db_session)
    unrelated = create_user(
        db_session,
        name="Unrelated Rider",
        email="sos-unrelated@sd.taylors.edu.my",
        role=UserRole.rider,
        gender=Gender.female,
        student_id="SOS-U",
    )

    response = client.post(
        "/api/sos",
        json=sos_payload(trip.trip_id),
        headers=auth_headers_for(unrelated),
    )

    assert response.status_code == 403


def test_admin_can_list_and_resolve_sos_event(client, db_session: Session):
    admin = create_admin_user(db_session)
    _, rider, trip = create_trip_with_confirmed_rider(db_session)
    create_response = client.post(
        "/api/sos",
        json=sos_payload(trip.trip_id),
        headers=auth_headers_for(rider),
    )
    sos_id = create_response.json()["sos_id"]

    list_response = client.get("/api/sos", headers=auth_headers_for(admin))
    update_response = client.patch(
        f"/api/sos/{sos_id}/status",
        json={"status": "resolved"},
        headers=auth_headers_for(admin),
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "resolved"
    assert update_response.json()["resolved_time"] is not None


def test_non_admin_cannot_update_sos_status(client, db_session: Session):
    _, rider, trip = create_trip_with_confirmed_rider(db_session)
    create_response = client.post(
        "/api/sos",
        json=sos_payload(trip.trip_id),
        headers=auth_headers_for(rider),
    )
    sos_id = create_response.json()["sos_id"]

    response = client.patch(
        f"/api/sos/{sos_id}/status",
        json={"status": "resolved"},
        headers=auth_headers_for(rider),
    )

    assert response.status_code == 403


def test_admin_websocket_receives_sos_alert(client, db_session: Session):
    admin = create_admin_user(db_session)
    _, rider, trip = create_trip_with_confirmed_rider(db_session)

    with client.websocket_connect(f"/ws/admin/sos?token={bearer_token(admin)}") as websocket:
        create_response = client.post(
            "/api/sos",
            json=sos_payload(trip.trip_id),
            headers=auth_headers_for(rider),
        )
        message = websocket.receive_json()

    assert create_response.status_code == 201
    assert message["status"] == "new"
    assert message["trip_id"] == trip.trip_id
