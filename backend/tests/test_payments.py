from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.enums import Gender, MatchStatus, RideRequestStatus, TripStatus, UserRole
from app.models.match import RideMatch
from app.models.ride_request import RideRequest
from app.models.trip import Trip
from app.core.config import settings
from app.services.payments import calculate_fare
from tests.conftest import auth_headers_for, create_admin_user, create_user


def create_confirmed_match(db_session: Session, *, confirmed: bool = True, distance_km: float | None = 10.0):
    rider = create_user(
        db_session,
        name="Aina Payment",
        email="payment-rider@sd.taylors.edu.my",
        role=UserRole.rider,
        gender=Gender.female,
        student_id="PAY-R",
    )
    driver = create_user(
        db_session,
        name="Driver Payment",
        email="payment-driver@sd.taylors.edu.my",
        role=UserRole.driver,
        gender=Gender.male,
        student_id="PAY-D",
    )
    ride_request = RideRequest(
        rider_id=rider.user_id,
        origin="Taylor's Lakeside Campus",
        destination="KL Sentral",
        preferred_time=datetime.now(UTC) + timedelta(hours=2),
        passenger_count=2,
        distance_km=distance_km,
        status=RideRequestStatus.matched if confirmed else RideRequestStatus.pending,
    )
    trip = Trip(
        driver_id=driver.user_id,
        origin="Taylor's Lakeside Campus",
        destination="KL Sentral",
        departure_time=ride_request.preferred_time,
        available_seats=2,
        total_seats=4,
        status=TripStatus.matched,
    )
    db_session.add_all([ride_request, trip])
    db_session.commit()
    db_session.refresh(ride_request)
    db_session.refresh(trip)

    match = RideMatch(
        trip_id=trip.trip_id,
        request_id=ride_request.request_id,
        rider_id=rider.user_id,
        match_score=95.0,
        status=MatchStatus.confirmed if confirmed else MatchStatus.recommended,
    )
    db_session.add(match)
    db_session.commit()
    db_session.refresh(match)
    return rider, driver, ride_request, trip, match


def test_calculate_fare_returns_total_and_per_passenger():
    fare = calculate_fare(distance_km=10, passenger_count=2)

    assert fare.base_fare == 3.0
    assert fare.rate_per_km == 1.2
    assert fare.total_fare == 15.0
    assert fare.fare_per_passenger == 7.5


def test_rider_can_simulate_ewallet_payment_for_confirmed_match(client, db_session: Session):
    rider, _, _, _, match = create_confirmed_match(db_session, distance_km=10.0)

    response = client.post(
        f"/api/payments/matches/{match.match_id}/simulate",
        json={},
        headers=auth_headers_for(rider),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_fare"] == 15.0
    assert body["fare_per_passenger"] == 7.5
    assert body["payment"]["payment_status"] == "paid"
    assert body["payment"]["payment_method"] == "simulated_ewallet"
    assert body["payment"]["amount"] == 7.5


def test_payment_requires_confirmed_match(client, db_session: Session):
    rider, _, _, _, match = create_confirmed_match(db_session, confirmed=False)

    response = client.post(
        f"/api/payments/matches/{match.match_id}/simulate",
        json={},
        headers=auth_headers_for(rider),
    )

    assert response.status_code == 400


def test_unrelated_user_cannot_pay_another_riders_match(client, db_session: Session):
    _, _, _, _, match = create_confirmed_match(db_session)
    unrelated = create_user(
        db_session,
        name="Unrelated Payer",
        email="unrelated-payer@sd.taylors.edu.my",
        role=UserRole.rider,
        gender=Gender.female,
        student_id="PAY-X",
    )

    response = client.post(
        f"/api/payments/matches/{match.match_id}/simulate",
        json={},
        headers=auth_headers_for(unrelated),
    )

    assert response.status_code == 403


def test_admin_cannot_create_payment_for_rider_match(client, db_session: Session):
    admin = create_admin_user(db_session)
    _, _, _, _, match = create_confirmed_match(db_session)

    response = client.post(
        f"/api/payments/matches/{match.match_id}/simulate",
        json={},
        headers=auth_headers_for(admin),
    )

    assert response.status_code == 403


def test_production_disables_simulated_payments(client, db_session: Session, monkeypatch):
    rider, _, _, _, match = create_confirmed_match(db_session)
    monkeypatch.setattr(settings, "environment", "production")

    response = client.post(
        f"/api/payments/matches/{match.match_id}/simulate",
        json={},
        headers=auth_headers_for(rider),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Simulated payments are disabled in production"


def test_payment_can_use_provided_distance_when_request_has_no_distance(client, db_session: Session):
    rider, _, ride_request, _, match = create_confirmed_match(db_session, distance_km=None)

    response = client.post(
        f"/api/payments/matches/{match.match_id}/simulate",
        json={"distance_km": 5},
        headers=auth_headers_for(rider),
    )
    db_session.refresh(ride_request)

    assert response.status_code == 200
    assert response.json()["total_fare"] == 9.0
    assert ride_request.distance_km == 5


def test_admin_can_list_payments(client, db_session: Session):
    admin = create_admin_user(db_session)
    rider, _, _, _, match = create_confirmed_match(db_session)
    client.post(
        f"/api/payments/matches/{match.match_id}/simulate",
        json={},
        headers=auth_headers_for(rider),
    )

    response = client.get("/api/payments", headers=auth_headers_for(admin))

    assert response.status_code == 200
    assert len(response.json()) == 1
