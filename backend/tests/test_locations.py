from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.enums import Gender, MatchStatus, RideRequestStatus, TripStatus, UserRole
from app.models.match import RideMatch
from app.models.ride_request import RideRequest
from app.models.trip import Trip
from tests.conftest import auth_headers_for, create_admin_user, create_user


def bearer_token(user) -> str:
    return auth_headers_for(user)["Authorization"].split(" ", 1)[1]


def create_ongoing_trip(db_session: Session):
    driver = create_user(
        db_session,
        name="Location Driver",
        email="location-driver@sd.taylors.edu.my",
        role=UserRole.driver,
        gender=Gender.male,
        student_id="LOC-D",
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
    return driver, trip


def create_confirmed_rider_for_trip(db_session: Session, trip: Trip):
    rider = create_user(
        db_session,
        name="Location Rider",
        email="location-rider@sd.taylors.edu.my",
        role=UserRole.rider,
        gender=Gender.female,
        student_id="LOC-R",
    )
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
    return rider


def test_driver_can_create_location_and_read_latest(client, db_session: Session):
    driver, trip = create_ongoing_trip(db_session)

    create_response = client.post(
        "/api/locations",
        json={"trip_id": trip.trip_id, "latitude": 3.0621, "longitude": 101.6167},
        headers=auth_headers_for(driver),
    )
    latest_response = client.get(
        f"/api/locations/trips/{trip.trip_id}/latest",
        headers=auth_headers_for(driver),
    )

    assert create_response.status_code == 201
    assert latest_response.status_code == 200
    assert latest_response.json()["latitude"] == 3.0621


def test_location_requires_ongoing_trip(client, db_session: Session):
    driver, trip = create_ongoing_trip(db_session)
    trip.status = TripStatus.posted
    db_session.add(trip)
    db_session.commit()

    response = client.post(
        "/api/locations",
        json={"trip_id": trip.trip_id, "latitude": 3.0621, "longitude": 101.6167},
        headers=auth_headers_for(driver),
    )

    assert response.status_code == 400


def test_confirmed_rider_can_read_latest_driver_location(client, db_session: Session):
    driver, trip = create_ongoing_trip(db_session)
    rider = create_confirmed_rider_for_trip(db_session, trip)
    client.post(
        "/api/locations",
        json={"trip_id": trip.trip_id, "latitude": 3.0621, "longitude": 101.6167},
        headers=auth_headers_for(driver),
    )

    response = client.get(
        f"/api/locations/trips/{trip.trip_id}/latest",
        headers=auth_headers_for(rider),
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == driver.user_id


def test_confirmed_rider_cannot_send_driver_location(client, db_session: Session):
    _, trip = create_ongoing_trip(db_session)
    rider = create_confirmed_rider_for_trip(db_session, trip)

    response = client.post(
        "/api/locations",
        json={"trip_id": trip.trip_id, "latitude": 3.0621, "longitude": 101.6167},
        headers=auth_headers_for(rider),
    )

    assert response.status_code == 403


def test_unrelated_user_cannot_read_latest_driver_location(client, db_session: Session):
    driver, trip = create_ongoing_trip(db_session)
    unrelated = create_user(
        db_session,
        name="Location Stranger",
        email="location-stranger@sd.taylors.edu.my",
        role=UserRole.rider,
        gender=Gender.female,
        student_id="LOC-X",
    )
    client.post(
        "/api/locations",
        json={"trip_id": trip.trip_id, "latitude": 3.0621, "longitude": 101.6167},
        headers=auth_headers_for(driver),
    )

    response = client.get(
        f"/api/locations/trips/{trip.trip_id}/latest",
        headers=auth_headers_for(unrelated),
    )

    assert response.status_code == 403


def test_admin_can_read_latest_trip_location(client, db_session: Session):
    admin = create_admin_user(db_session)
    driver, trip = create_ongoing_trip(db_session)
    client.post(
        "/api/locations",
        json={"trip_id": trip.trip_id, "latitude": 3.0621, "longitude": 101.6167},
        headers=auth_headers_for(driver),
    )

    response = client.get(
        f"/api/locations/trips/{trip.trip_id}/latest",
        headers=auth_headers_for(admin),
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == driver.user_id


def test_admin_can_list_trip_location_logs(client, db_session: Session):
    admin = create_admin_user(db_session)
    driver, trip = create_ongoing_trip(db_session)
    client.post(
        "/api/locations",
        json={"trip_id": trip.trip_id, "latitude": 3.0621, "longitude": 101.6167},
        headers=auth_headers_for(driver),
    )

    response = client.get(
        f"/api/locations/trips/{trip.trip_id}/logs",
        headers=auth_headers_for(admin),
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_websocket_location_broadcasts_latest_point(client, db_session: Session):
    driver, trip = create_ongoing_trip(db_session)
    token = bearer_token(driver)

    with client.websocket_connect(f"/ws/locations/{trip.trip_id}?token={token}") as websocket:
        websocket.send_json({"latitude": 3.0621, "longitude": 101.6167})
        message = websocket.receive_json()

    assert message["trip_id"] == trip.trip_id
    assert message["user_id"] == driver.user_id
    assert message["latitude"] == 3.0621
