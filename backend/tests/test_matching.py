from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.enums import Gender, RideRequestStatus, TripStatus, UserRole
from app.models.ride_request import RideRequest
from app.models.trip import Trip
from app.models.user import User
from app.services.matching import (
    RouteCoordinates,
    RouteInsertionEstimate,
    angle_between_routes,
    calculate_driver_acceptance_score,
    calculate_driver_detour_score,
    calculate_final_match_score,
    calculate_passenger_convenience_score,
    calculate_route_alignment_score,
    calculate_route_order_score,
    evaluate_match_candidate,
    estimate_route_insertion,
)
from tests.conftest import auth_headers_for, create_user


def create_rider(db_session: Session, *, gender: Gender = Gender.female) -> User:
    return create_user(
        db_session,
        name="Nur Aina",
        email=f"rider-match-{gender.value}@sd.taylors.edu.my",
        role=UserRole.rider,
        gender=gender,
        student_id=f"RM-{gender.value}",
    )


def create_driver(
    db_session: Session,
    *,
    index: int,
    gender: Gender = Gender.female,
    rating: float = 5.0,
) -> User:
    driver = create_user(
        db_session,
        name=f"Driver {index}",
        email=f"driver-match-{index}@sd.taylors.edu.my",
        role=UserRole.driver,
        gender=gender,
        student_id=f"DM-{index}",
    )
    driver.rating = rating
    db_session.add(driver)
    db_session.commit()
    db_session.refresh(driver)
    return driver


def create_request(
    db_session: Session,
    rider: User,
    *,
    passenger_count: int = 1,
    preferred_time: datetime | None = None,
    gender_preference: str = "none",
    origin_latitude: float | None = None,
    origin_longitude: float | None = None,
    destination_latitude: float | None = None,
    destination_longitude: float | None = None,
) -> RideRequest:
    ride_request = RideRequest(
        rider_id=rider.user_id,
        origin="Taylor's Lakeside Campus",
        destination="Sunway Pyramid",
        origin_latitude=origin_latitude,
        origin_longitude=origin_longitude,
        destination_latitude=destination_latitude,
        destination_longitude=destination_longitude,
        preferred_time=preferred_time or datetime.now(UTC) + timedelta(hours=2),
        passenger_count=passenger_count,
        gender_preference=gender_preference,
        status=RideRequestStatus.pending,
    )
    db_session.add(ride_request)
    db_session.commit()
    db_session.refresh(ride_request)
    return ride_request


def create_trip(
    db_session: Session,
    driver: User,
    *,
    available_seats: int = 4,
    departure_time: datetime | None = None,
    origin: str = "Taylor's Lakeside Campus",
    destination: str = "Sunway Pyramid",
    origin_latitude: float | None = None,
    origin_longitude: float | None = None,
    destination_latitude: float | None = None,
    destination_longitude: float | None = None,
) -> Trip:
    trip = Trip(
        driver_id=driver.user_id,
        origin=origin,
        destination=destination,
        origin_latitude=origin_latitude,
        origin_longitude=origin_longitude,
        destination_latitude=destination_latitude,
        destination_longitude=destination_longitude,
        departure_time=departure_time or datetime.now(UTC) + timedelta(hours=2),
        available_seats=available_seats,
        total_seats=available_seats,
        status=TripStatus.posted,
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)
    return trip


def test_rider_recommendations_apply_constraints_and_return_top_five(client, db_session: Session):
    rider = create_rider(db_session)
    ride_request = create_request(db_session, rider, passenger_count=2)
    base_time = ride_request.preferred_time

    for index in range(6):
        driver = create_driver(db_session, index=index, rating=5.0 - index * 0.2)
        create_trip(
            db_session,
            driver,
            departure_time=base_time + timedelta(minutes=index),
        )

    male_driver = create_driver(db_session, index=20, gender=Gender.male)
    same_gender_request = create_request(
        db_session,
        rider,
        passenger_count=2,
        preferred_time=base_time,
        gender_preference="same_gender",
    )
    create_trip(db_session, male_driver, departure_time=base_time)

    far_driver = create_driver(db_session, index=21)
    create_trip(db_session, far_driver, departure_time=base_time + timedelta(minutes=45))

    small_car_driver = create_driver(db_session, index=22)
    create_trip(db_session, small_car_driver, available_seats=1, departure_time=base_time)

    response = client.get(
        f"/api/matches/ride-requests/{ride_request.request_id}/recommendations",
        headers=auth_headers_for(rider),
    )
    same_gender_response = client.get(
        f"/api/matches/ride-requests/{same_gender_request.request_id}/recommendations",
        headers=auth_headers_for(rider),
    )

    assert response.status_code == 200
    matches = response.json()
    assert len(matches) == 5
    scores = [match["match_score"] for match in matches]
    assert scores == sorted(scores, reverse=True)
    assert same_gender_response.status_code == 200
    assert all(match["trip_id"] != male_driver.trips[0].trip_id for match in same_gender_response.json())


def test_driver_can_get_recommended_requests(client, db_session: Session):
    rider = create_rider(db_session)
    ride_request = create_request(db_session, rider, passenger_count=1)
    driver = create_driver(db_session, index=1)
    trip = create_trip(db_session, driver, departure_time=ride_request.preferred_time)

    response = client.get(
        f"/api/matches/trips/{trip.trip_id}/recommendations",
        headers=auth_headers_for(driver),
    )

    assert response.status_code == 200
    assert response.json()[0]["request_id"] == ride_request.request_id


def test_coordinate_route_alignment_prioritizes_closer_trip(client, db_session: Session):
    rider = create_rider(db_session)
    ride_request = create_request(
        db_session,
        rider,
        origin_latitude=3.0646,
        origin_longitude=101.6159,
        destination_latitude=3.0738,
        destination_longitude=101.6070,
    )
    base_time = ride_request.preferred_time
    close_driver = create_driver(db_session, index=30, rating=4.7)
    farther_driver = create_driver(db_session, index=31, rating=4.7)
    close_trip = create_trip(
        db_session,
        close_driver,
        departure_time=base_time,
        origin_latitude=3.0648,
        origin_longitude=101.6160,
        destination_latitude=3.0740,
        destination_longitude=101.6071,
    )
    farther_trip = create_trip(
        db_session,
        farther_driver,
        departure_time=base_time,
        origin_latitude=3.0635,
        origin_longitude=101.6170,
        destination_latitude=3.0730,
        destination_longitude=101.6080,
    )

    response = client.get(
        f"/api/matches/ride-requests/{ride_request.request_id}/recommendations",
        headers=auth_headers_for(rider),
    )

    assert response.status_code == 200
    matches = response.json()
    assert [match["trip_id"] for match in matches[:2]] == [close_trip.trip_id, farther_trip.trip_id]
    assert matches[0]["match_score"] > matches[1]["match_score"]
    assert "score_breakdown" in matches[0]
    assert "route_alignment_score" in matches[0]["score_breakdown"]
    assert matches[0]["reasons"]


def test_coordinate_route_alignment_excludes_far_detour_even_with_same_labels(client, db_session: Session):
    rider = create_rider(db_session)
    ride_request = create_request(
        db_session,
        rider,
        origin_latitude=3.0646,
        origin_longitude=101.6159,
        destination_latitude=3.0738,
        destination_longitude=101.6070,
    )
    far_driver = create_driver(db_session, index=32)
    far_trip = create_trip(
        db_session,
        far_driver,
        departure_time=ride_request.preferred_time,
        origin_latitude=3.1800,
        origin_longitude=101.7200,
        destination_latitude=3.2100,
        destination_longitude=101.7600,
    )

    response = client.get(
        f"/api/matches/ride-requests/{ride_request.request_id}/recommendations",
        headers=auth_headers_for(rider),
    )

    assert response.status_code == 200
    assert all(match["trip_id"] != far_trip.trip_id for match in response.json())


def test_route_alignment_scores_same_direction_and_rejects_opposite_direction(db_session: Session):
    same_direction_angle = angle_between_routes(
        (3.0640, 101.6160),
        (3.0780, 101.6020),
        (3.0650, 101.6150),
        (3.0730, 101.6070),
    )
    opposite_direction_angle = angle_between_routes(
        (3.0780, 101.6020),
        (3.0640, 101.6160),
        (3.0650, 101.6150),
        (3.0730, 101.6070),
    )

    assert calculate_route_alignment_score(same_direction_angle) > 0.95
    assert calculate_route_alignment_score(opposite_direction_angle) == 0

    rider = create_rider(db_session)
    ride_request = create_request(
        db_session,
        rider,
        origin_latitude=3.0650,
        origin_longitude=101.6150,
        destination_latitude=3.0730,
        destination_longitude=101.6070,
    )
    driver = create_driver(db_session, index=40)
    opposite_trip = create_trip(
        db_session,
        driver,
        departure_time=ride_request.preferred_time,
        origin_latitude=3.0780,
        origin_longitude=101.6020,
        destination_latitude=3.0640,
        destination_longitude=101.6160,
    )

    evaluation = evaluate_match_candidate(ride_request, opposite_trip)

    assert evaluation.reject_reason == "opposite_direction"


def test_route_order_scores_pickup_before_dropoff():
    ordered = estimate_route_insertion(
        RouteCoordinates(
            driver_origin=(3.0640, 101.6000),
            driver_destination=(3.0640, 101.6600),
            passenger_pickup=(3.0642, 101.6200),
            passenger_dropoff=(3.0642, 101.6400),
        )
    )
    reversed_order = estimate_route_insertion(
        RouteCoordinates(
            driver_origin=(3.0640, 101.6000),
            driver_destination=(3.0640, 101.6600),
            passenger_pickup=(3.0642, 101.6400),
            passenger_dropoff=(3.0642, 101.6200),
        )
    )

    assert calculate_route_order_score(0.8, 0.2) == 0
    assert ordered.route_order_score > 0.9
    assert reversed_order.route_order_score == 0


def test_detour_constraint_allows_small_detour_and_rejects_large_detour(db_session: Session):
    rider = create_rider(db_session)
    ride_request = create_request(
        db_session,
        rider,
        origin_latitude=3.0646,
        origin_longitude=101.6159,
        destination_latitude=3.0738,
        destination_longitude=101.6070,
    )
    driver = create_driver(db_session, index=41)
    small_detour_trip = create_trip(
        db_session,
        driver,
        departure_time=ride_request.preferred_time,
        origin_latitude=3.0648,
        origin_longitude=101.6160,
        destination_latitude=3.0740,
        destination_longitude=101.6071,
    )
    large_detour_driver = create_driver(db_session, index=42)
    large_detour_trip = create_trip(
        db_session,
        large_detour_driver,
        departure_time=ride_request.preferred_time,
        origin_latitude=3.0300,
        origin_longitude=101.5800,
        destination_latitude=3.0550,
        destination_longitude=101.5950,
    )

    assert evaluate_match_candidate(ride_request, small_detour_trip).reject_reason is None
    assert evaluate_match_candidate(ride_request, large_detour_trip).reject_reason == "too_much_driver_detour"


def test_route_proximity_allows_near_pickup_and_rejects_far_pickup(db_session: Session):
    rider = create_rider(db_session)
    near_request = create_request(
        db_session,
        rider,
        origin_latitude=3.0642,
        origin_longitude=101.6200,
        destination_latitude=3.0642,
        destination_longitude=101.6400,
    )
    far_pickup_request = create_request(
        db_session,
        rider,
        origin_latitude=3.0780,
        origin_longitude=101.6200,
        destination_latitude=3.0780,
        destination_longitude=101.6400,
        preferred_time=near_request.preferred_time,
    )
    driver = create_driver(db_session, index=43)
    trip = create_trip(
        db_session,
        driver,
        departure_time=near_request.preferred_time,
        origin_latitude=3.0640,
        origin_longitude=101.6000,
        destination_latitude=3.0640,
        destination_longitude=101.6600,
    )

    assert evaluate_match_candidate(near_request, trip).reject_reason is None
    assert evaluate_match_candidate(far_pickup_request, trip).reject_reason == "passenger_walk_too_far"


def test_passenger_convenience_rewards_short_wait_and_penalizes_longer_shared_duration():
    route_insertion = estimate_route_insertion(
        RouteCoordinates(
            driver_origin=(3.0648, 101.6160),
            driver_destination=(3.0740, 101.6071),
            passenger_pickup=(3.0646, 101.6159),
            passenger_dropoff=(3.0738, 101.6070),
        )
    )
    short_wait_score = calculate_passenger_convenience_score(route_insertion, waiting_time_minutes=3)
    long_wait_score = calculate_passenger_convenience_score(route_insertion, waiting_time_minutes=25)
    slower_shared_route = RouteInsertionEstimate(
        original_driver_distance_km=route_insertion.original_driver_distance_km,
        original_driver_duration_min=route_insertion.original_driver_duration_min,
        shared_route_distance_km=route_insertion.shared_route_distance_km,
        shared_route_duration_min=route_insertion.shared_route_duration_min,
        detour_distance_km=route_insertion.detour_distance_km,
        detour_duration_min=route_insertion.detour_duration_min,
        passenger_direct_duration_min=route_insertion.passenger_direct_duration_min,
        shared_passenger_duration_min=route_insertion.passenger_direct_duration_min * 1.7,
        pickup_walk_distance_km=route_insertion.pickup_walk_distance_km,
        dropoff_walk_distance_km=route_insertion.dropoff_walk_distance_km,
    )

    assert short_wait_score > long_wait_score
    assert calculate_passenger_convenience_score(slower_shared_route, 3) < short_wait_score


def test_driver_acceptance_rewards_low_detour_and_passenger_reliability(db_session: Session):
    reliable_rider = create_rider(db_session)
    reliable_request = create_request(
        db_session,
        reliable_rider,
        origin_latitude=3.0646,
        origin_longitude=101.6159,
        destination_latitude=3.0738,
        destination_longitude=101.6070,
    )
    unreliable_rider = create_user(
        db_session,
        name="Unreliable Rider",
        email="unreliable-rider@sd.taylors.edu.my",
        role=UserRole.rider,
        gender=Gender.female,
        student_id="UNREL-1",
    )
    unreliable_rider.rating = 3.0
    for index in range(3):
        db_session.add(
            RideRequest(
                rider_id=unreliable_rider.user_id,
                origin="Taylor's Lakeside Campus",
                destination="Sunway Pyramid",
                preferred_time=reliable_request.preferred_time + timedelta(days=index + 1),
                passenger_count=1,
                gender_preference="none",
                status=RideRequestStatus.cancelled,
            )
        )
    db_session.commit()
    unreliable_request = create_request(
        db_session,
        unreliable_rider,
        origin_latitude=3.0646,
        origin_longitude=101.6159,
        destination_latitude=3.0738,
        destination_longitude=101.6070,
        preferred_time=reliable_request.preferred_time,
    )
    driver = create_driver(db_session, index=44)
    trip = create_trip(
        db_session,
        driver,
        departure_time=reliable_request.preferred_time,
        origin_latitude=3.0648,
        origin_longitude=101.6160,
        destination_latitude=3.0740,
        destination_longitude=101.6071,
    )
    low_detour = evaluate_match_candidate(reliable_request, trip).route_insertion
    high_detour = RouteInsertionEstimate(
        original_driver_distance_km=low_detour.original_driver_distance_km,
        original_driver_duration_min=low_detour.original_driver_duration_min,
        shared_route_distance_km=low_detour.shared_route_distance_km + 2.5,
        shared_route_duration_min=low_detour.shared_route_duration_min + 8,
        detour_distance_km=2.5,
        detour_duration_min=8,
        passenger_direct_duration_min=low_detour.passenger_direct_duration_min,
        shared_passenger_duration_min=low_detour.shared_passenger_duration_min,
        pickup_walk_distance_km=low_detour.pickup_walk_distance_km,
        dropoff_walk_distance_km=low_detour.dropoff_walk_distance_km,
    )

    assert calculate_driver_detour_score(low_detour) > calculate_driver_detour_score(high_detour)
    assert calculate_driver_acceptance_score(reliable_request, trip, low_detour) > calculate_driver_acceptance_score(
        unreliable_request,
        trip,
        low_detour,
    )


def test_minimum_score_filters_low_quality_fallback_candidate(client, db_session: Session):
    rider = create_rider(db_session)
    ride_request = create_request(
        db_session,
        rider,
        origin_latitude=None,
        origin_longitude=None,
        destination_latitude=None,
        destination_longitude=None,
    )
    driver = create_driver(db_session, index=45)
    create_trip(
        db_session,
        driver,
        origin="KL Sentral",
        destination="Petaling Jaya",
        departure_time=ride_request.preferred_time,
    )

    response = client.get(
        f"/api/matches/ride-requests/{ride_request.request_id}/recommendations",
        headers=auth_headers_for(rider),
    )

    assert response.status_code == 200
    assert response.json() == []
    assert calculate_final_match_score(
        {
            "route_alignment_score": 0,
            "driver_detour_score": 0,
            "passenger_convenience_score": 0,
            "time_fit_score": 1,
            "driver_acceptance_score": 0,
            "supply_efficiency_score": 0,
            "trust_safety_score": 1,
        }
    ) < 65


def test_capacity_score_prefers_tighter_seat_fit_when_other_signals_match(client, db_session: Session):
    rider = create_rider(db_session)
    ride_request = create_request(db_session, rider, passenger_count=3)
    exact_fit_driver = create_driver(db_session, index=33, rating=4.8)
    loose_fit_driver = create_driver(db_session, index=34, rating=4.8)
    exact_fit_trip = create_trip(
        db_session,
        exact_fit_driver,
        available_seats=3,
        departure_time=ride_request.preferred_time,
    )
    loose_fit_trip = create_trip(
        db_session,
        loose_fit_driver,
        available_seats=4,
        departure_time=ride_request.preferred_time,
    )

    response = client.get(
        f"/api/matches/ride-requests/{ride_request.request_id}/recommendations",
        headers=auth_headers_for(rider),
    )

    assert response.status_code == 200
    matches = response.json()
    assert [match["trip_id"] for match in matches[:2]] == [exact_fit_trip.trip_id, loose_fit_trip.trip_id]
    assert matches[0]["match_score"] > matches[1]["match_score"]


def test_confirm_match_updates_request_trip_and_full_status(client, db_session: Session):
    rider = create_rider(db_session)
    ride_request = create_request(db_session, rider, passenger_count=2)
    driver = create_driver(db_session, index=1)
    trip = create_trip(
        db_session,
        driver,
        available_seats=2,
        departure_time=ride_request.preferred_time,
    )
    recommendations = client.get(
        f"/api/matches/ride-requests/{ride_request.request_id}/recommendations",
        headers=auth_headers_for(rider),
    ).json()

    response = client.post(
        f"/api/matches/{recommendations[0]['match_id']}/confirm",
        headers=auth_headers_for(rider),
    )
    db_session.refresh(ride_request)
    db_session.refresh(trip)

    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"
    assert ride_request.status == RideRequestStatus.matched
    assert trip.available_seats == 0
    assert trip.status == TripStatus.full


def test_auto_assign_confirms_best_available_trip(client, db_session: Session):
    rider = create_rider(db_session)
    ride_request = create_request(
        db_session,
        rider,
        passenger_count=2,
        origin_latitude=3.0646,
        origin_longitude=101.6162,
        destination_latitude=3.0738,
        destination_longitude=101.607,
    )
    close_driver = create_driver(db_session, index=31, rating=4.9)
    farther_driver = create_driver(db_session, index=32, rating=4.9)
    close_trip = create_trip(
        db_session,
        close_driver,
        available_seats=4,
        departure_time=ride_request.preferred_time,
        origin_latitude=3.0648,
        origin_longitude=101.6164,
        destination_latitude=3.0738,
        destination_longitude=101.607,
    )
    create_trip(
        db_session,
        farther_driver,
        available_seats=4,
        departure_time=ride_request.preferred_time,
        origin_latitude=3.09,
        origin_longitude=101.64,
        destination_latitude=3.0738,
        destination_longitude=101.607,
    )

    response = client.post(
        f"/api/matches/ride-requests/{ride_request.request_id}/auto-assign",
        headers=auth_headers_for(rider),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "confirmed"
    assert payload["trip_id"] == close_trip.trip_id

    db_session.refresh(ride_request)
    db_session.refresh(close_trip)
    assert ride_request.status == RideRequestStatus.matched
    assert close_trip.status == TripStatus.matched
    assert close_trip.available_seats == 2


def test_confirm_match_rechecks_capacity_before_reserving_seat(client, db_session: Session):
    driver = create_driver(db_session, index=41)
    rider_one = create_rider(db_session, gender=Gender.female)
    rider_two = create_user(
        db_session,
        name="Second Rider",
        email="second-capacity-rider@sd.taylors.edu.my",
        role=UserRole.rider,
        gender=Gender.female,
        student_id="SECOND-CAP",
    )
    request_one = create_request(db_session, rider_one, passenger_count=1)
    request_two = create_request(db_session, rider_two, passenger_count=1, preferred_time=request_one.preferred_time)
    create_trip(db_session, driver, available_seats=1, departure_time=request_one.preferred_time)
    first_recommendation = client.get(
        f"/api/matches/ride-requests/{request_one.request_id}/recommendations",
        headers=auth_headers_for(rider_one),
    ).json()[0]
    second_recommendation = client.get(
        f"/api/matches/ride-requests/{request_two.request_id}/recommendations",
        headers=auth_headers_for(rider_two),
    ).json()[0]

    first_response = client.post(
        f"/api/matches/{first_recommendation['match_id']}/confirm",
        headers=auth_headers_for(rider_one),
    )
    second_response = client.post(
        f"/api/matches/{second_recommendation['match_id']}/confirm",
        headers=auth_headers_for(rider_two),
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Trip is not available"


def test_driver_can_reject_recommended_match(client, db_session: Session):
    rider = create_rider(db_session)
    ride_request = create_request(db_session, rider)
    driver = create_driver(db_session, index=1)
    create_trip(db_session, driver, departure_time=ride_request.preferred_time)
    recommendations = client.get(
        f"/api/matches/ride-requests/{ride_request.request_id}/recommendations",
        headers=auth_headers_for(rider),
    ).json()

    response = client.post(
        f"/api/matches/{recommendations[0]['match_id']}/reject",
        headers=auth_headers_for(driver),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


def test_unrelated_rider_and_driver_cannot_confirm_match(client, db_session: Session):
    rider = create_rider(db_session)
    ride_request = create_request(db_session, rider)
    driver = create_driver(db_session, index=1)
    create_trip(db_session, driver, departure_time=ride_request.preferred_time)
    recommendations = client.get(
        f"/api/matches/ride-requests/{ride_request.request_id}/recommendations",
        headers=auth_headers_for(rider),
    ).json()
    match_id = recommendations[0]["match_id"]
    unrelated_rider = create_user(
        db_session,
        name="Unrelated Rider",
        email="unrelated-confirm-rider@sd.taylors.edu.my",
        role=UserRole.rider,
        gender=Gender.female,
        student_id="UR-CONF",
    )
    unrelated_driver = create_driver(db_session, index=99)

    rider_response = client.post(
        f"/api/matches/{match_id}/confirm",
        headers=auth_headers_for(unrelated_rider),
    )
    driver_response = client.post(
        f"/api/matches/{match_id}/confirm",
        headers=auth_headers_for(unrelated_driver),
    )

    assert rider_response.status_code == 403
    assert driver_response.status_code == 403


def test_unrelated_driver_cannot_reject_match(client, db_session: Session):
    rider = create_rider(db_session)
    ride_request = create_request(db_session, rider)
    owner_driver = create_driver(db_session, index=1)
    unrelated_driver = create_driver(db_session, index=2)
    create_trip(db_session, owner_driver, departure_time=ride_request.preferred_time)
    recommendations = client.get(
        f"/api/matches/ride-requests/{ride_request.request_id}/recommendations",
        headers=auth_headers_for(rider),
    ).json()

    response = client.post(
        f"/api/matches/{recommendations[0]['match_id']}/reject",
        headers=auth_headers_for(unrelated_driver),
    )

    assert response.status_code == 403
