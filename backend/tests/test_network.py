from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.enums import Gender, MatchStatus, RideRequestStatus, TripStatus, UserRole, VerificationStatus
from app.models.match import RideMatch
from app.models.ride_request import RideRequest
from app.models.trip import Trip
from app.models.vehicle import Vehicle
from tests.conftest import auth_headers_for, create_user


def create_network_trip(db_session: Session):
    driver = create_user(
        db_session,
        name="Network Driver",
        email="network-driver@sd.taylors.edu.my",
        role=UserRole.driver,
        gender=Gender.male,
        student_id="NET-D",
    )
    rider = create_user(
        db_session,
        name="Network Rider",
        email="network-rider@sd.taylors.edu.my",
        role=UserRole.rider,
        gender=Gender.female,
        student_id="NET-R",
    )
    trip = Trip(
        driver_id=driver.user_id,
        origin="Taylor's Lakeside Campus",
        destination="Sunway Pyramid",
        departure_time=datetime.now(UTC) + timedelta(minutes=15),
        available_seats=2,
        total_seats=4,
        status=TripStatus.matched,
    )
    db_session.add(trip)
    db_session.add(
        Vehicle(
            driver_id=driver.user_id,
            plate_number="NET123",
            vehicle_model="Perodua Myvi",
            seat_count=4,
            verification_status=VerificationStatus.approved,
        )
    )
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
    db_session.add(
        RideMatch(
            trip_id=trip.trip_id,
            request_id=ride_request.request_id,
            rider_id=rider.user_id,
            match_score=90,
            status=MatchStatus.confirmed,
        )
    )
    db_session.commit()
    return driver, rider, trip


def test_network_trips_are_visible_to_driver_and_confirmed_rider(client, db_session: Session):
    driver, rider, trip = create_network_trip(db_session)

    rider_response = client.get("/api/network/me/trips", headers=auth_headers_for(rider))
    driver_response = client.get("/api/network/me/trips", headers=auth_headers_for(driver))

    assert rider_response.status_code == 200
    assert driver_response.status_code == 200
    assert rider_response.json()[0]["trip_id"] == trip.trip_id
    assert driver_response.json()[0]["trip_id"] == trip.trip_id
    assert rider_response.json()[0]["vehicle"]["plate_number"] == "NET123"
    assert rider_response.json()[0]["riders"][0]["name"] == rider.name
    assert driver_response.json()[0]["driver"]["name"] == driver.name


def test_trip_network_messages_are_shared_between_rider_and_driver(client, db_session: Session):
    driver, rider, trip = create_network_trip(db_session)

    create_response = client.post(
        f"/api/network/trips/{trip.trip_id}/messages",
        json={"body": "I am at the pickup point."},
        headers=auth_headers_for(driver),
    )
    list_response = client.get(
        f"/api/network/trips/{trip.trip_id}/messages",
        headers=auth_headers_for(rider),
    )

    assert create_response.status_code == 201
    assert list_response.status_code == 200
    assert list_response.json()[0]["body"] == "I am at the pickup point."
    assert list_response.json()[0]["sender_role"] == "driver"
