from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.enums import Gender, MatchStatus, RideRequestStatus, TripStatus, UserRole
from app.models.match import RideMatch
from app.models.ride_request import RideRequest
from app.models.trip import Trip
from tests.conftest import auth_headers_for, create_admin_user, create_user


def create_completed_trip(db_session: Session, *, status: TripStatus = TripStatus.completed):
    driver = create_user(
        db_session,
        name="Report Driver",
        email="report-driver@sd.taylors.edu.my",
        role=UserRole.driver,
        gender=Gender.male,
        student_id="REP-D",
    )
    rider = create_user(
        db_session,
        name="Report Rider",
        email="report-rider@sd.taylors.edu.my",
        role=UserRole.rider,
        gender=Gender.female,
        student_id="REP-R",
    )
    trip = Trip(
        driver_id=driver.user_id,
        origin="Taylor's Lakeside Campus",
        destination="KL Sentral",
        departure_time=datetime.now(UTC) - timedelta(hours=1),
        available_seats=2,
        total_seats=4,
        status=status,
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
        status=RideRequestStatus.completed if status == TripStatus.completed else RideRequestStatus.matched,
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


def test_rider_can_rate_driver_after_completed_trip(client, db_session: Session):
    driver, rider, trip = create_completed_trip(db_session)

    response = client.post(
        "/api/reports/ratings",
        json={"to_user_id": driver.user_id, "trip_id": trip.trip_id, "score": 4, "comment": "Good ride"},
        headers=auth_headers_for(rider),
    )
    db_session.refresh(driver)

    assert response.status_code == 201
    assert response.json()["score"] == 4
    assert driver.rating == 4.0


def test_driver_can_rate_rider_after_completed_trip(client, db_session: Session):
    driver, rider, trip = create_completed_trip(db_session)

    response = client.post(
        "/api/reports/ratings",
        json={"to_user_id": rider.user_id, "trip_id": trip.trip_id, "score": 5},
        headers=auth_headers_for(driver),
    )
    db_session.refresh(rider)

    assert response.status_code == 201
    assert rider.rating == 5.0


def test_cannot_rate_before_trip_completion(client, db_session: Session):
    driver, rider, trip = create_completed_trip(db_session, status=TripStatus.ongoing)

    response = client.post(
        "/api/reports/ratings",
        json={"to_user_id": driver.user_id, "trip_id": trip.trip_id, "score": 4},
        headers=auth_headers_for(rider),
    )

    assert response.status_code == 400


def test_unrelated_user_cannot_rate_trip_participant(client, db_session: Session):
    driver, _, trip = create_completed_trip(db_session)
    unrelated = create_user(
        db_session,
        name="Unrelated Reporter",
        email="unrelated-reporter@sd.taylors.edu.my",
        role=UserRole.rider,
        gender=Gender.female,
        student_id="REP-X",
    )

    response = client.post(
        "/api/reports/ratings",
        json={"to_user_id": driver.user_id, "trip_id": trip.trip_id, "score": 4},
        headers=auth_headers_for(unrelated),
    )

    assert response.status_code == 403


def test_user_cannot_rate_unrelated_person_for_trip(client, db_session: Session):
    _, rider, trip = create_completed_trip(db_session)
    unrelated = create_user(
        db_session,
        name="Unrelated Target",
        email="unrelated-target@sd.taylors.edu.my",
        role=UserRole.driver,
        gender=Gender.male,
        student_id="REP-T",
    )

    response = client.post(
        "/api/reports/ratings",
        json={"to_user_id": unrelated.user_id, "trip_id": trip.trip_id, "score": 4},
        headers=auth_headers_for(rider),
    )

    assert response.status_code == 403


def test_user_can_report_trip_participant(client, db_session: Session):
    driver, rider, trip = create_completed_trip(db_session)

    response = client.post(
        "/api/reports",
        json={
            "to_user_id": driver.user_id,
            "trip_id": trip.trip_id,
            "report_type": "unsafe",
            "comment": "Driver took a risky shortcut",
        },
        headers=auth_headers_for(rider),
    )

    assert response.status_code == 201
    assert response.json()["report_type"] == "unsafe"
    assert response.json()["score"] is None


def test_unrelated_user_cannot_report_trip_participant(client, db_session: Session):
    driver, _, trip = create_completed_trip(db_session)
    unrelated = create_user(
        db_session,
        name="Unrelated Report User",
        email="unrelated-report-user@sd.taylors.edu.my",
        role=UserRole.rider,
        gender=Gender.female,
        student_id="REP-U",
    )

    response = client.post(
        "/api/reports",
        json={
            "to_user_id": driver.user_id,
            "trip_id": trip.trip_id,
            "report_type": "unsafe",
            "comment": "Should not be accepted",
        },
        headers=auth_headers_for(unrelated),
    )

    assert response.status_code == 403


def test_admin_can_view_all_ratings_and_reports(client, db_session: Session):
    admin = create_admin_user(db_session)
    driver, rider, trip = create_completed_trip(db_session)
    client.post(
        "/api/reports",
        json={
            "to_user_id": driver.user_id,
            "trip_id": trip.trip_id,
            "report_type": "late",
            "comment": "Pickup was late",
        },
        headers=auth_headers_for(rider),
    )

    response = client.get("/api/reports", headers=auth_headers_for(admin))

    assert response.status_code == 200
    assert len(response.json()) == 1
