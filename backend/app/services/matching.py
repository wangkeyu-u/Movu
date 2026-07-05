from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import asin, atan2, cos, degrees, radians, sin, sqrt

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import GenderPreference, MatchStatus, RideRequestStatus, TripStatus
from app.models.match import RideMatch
from app.models.ride_request import RideRequest
from app.models.trip import Trip
from app.models.user import User


EARTH_RADIUS_KM = 6371.0
AVERAGE_CITY_SPEED_KMH = 30.0
AVERAGE_WALK_SPEED_KMH = 4.5
MATCH_TIME_WINDOW_MINUTES = settings.match_time_window_minutes
MAX_DRIVER_DETOUR_KM = settings.max_driver_detour_km
MAX_DRIVER_DETOUR_MINUTES = settings.max_driver_detour_minutes
MAX_PASSENGER_WALK_KM = settings.max_passenger_walk_km
MAX_PICKUP_OFFSET_KM = settings.max_pickup_offset_km
MAX_DROPOFF_OFFSET_KM = settings.max_dropoff_offset_km
MIN_MATCH_SCORE = settings.min_match_score
MATCH_SCORE_WEIGHTS = settings.match_score_weights


Coordinate = tuple[float, float]


@dataclass(frozen=True)
class RouteCoordinates:
    driver_origin: Coordinate
    driver_destination: Coordinate
    passenger_pickup: Coordinate
    passenger_dropoff: Coordinate


@dataclass(frozen=True)
class RouteInsertionEstimate:
    original_driver_distance_km: float
    original_driver_duration_min: float
    shared_route_distance_km: float
    shared_route_duration_min: float
    detour_distance_km: float
    detour_duration_min: float
    passenger_direct_duration_min: float
    shared_passenger_duration_min: float
    pickup_walk_distance_km: float
    dropoff_walk_distance_km: float
    pickup_route_progress: float = 0.0
    dropoff_route_progress: float = 0.0
    route_order_score: float = 1.0


@dataclass(frozen=True)
class MatchEvaluation:
    final_score: float
    score_breakdown: dict[str, float]
    reasons: list[str]
    reject_reason: str | None = None
    route_insertion: RouteInsertionEstimate | None = None


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _clamp_score(value: float) -> float:
    return max(0.0, min(100.0, value))


def _normalize_place(value: str) -> set[str]:
    cleaned = "".join(char.lower() if char.isalnum() else " " for char in value)
    return {part for part in cleaned.split() if part}


def place_score(left: str, right: str) -> float:
    left_tokens = _normalize_place(left)
    right_tokens = _normalize_place(right)
    if not left_tokens or not right_tokens:
        return 0.0
    if left_tokens == right_tokens:
        return 100.0
    overlap = len(left_tokens & right_tokens)
    if overlap == 0:
        return 0.0
    return min(90.0, 55.0 + 15.0 * overlap)


def haversine_distance_km(
    first_latitude: float,
    first_longitude: float,
    second_latitude: float,
    second_longitude: float,
) -> float:
    lat1 = radians(first_latitude)
    lon1 = radians(first_longitude)
    lat2 = radians(second_latitude)
    lon2 = radians(second_longitude)
    delta_latitude = lat2 - lat1
    delta_longitude = lon2 - lon1
    a = sin(delta_latitude / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_longitude / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def haversine_km(
    first_latitude: float,
    first_longitude: float,
    second_latitude: float,
    second_longitude: float,
) -> float:
    return haversine_distance_km(first_latitude, first_longitude, second_latitude, second_longitude)


def _coordinate_distance_km(first: Coordinate, second: Coordinate) -> float:
    return haversine_distance_km(first[0], first[1], second[0], second[1])


def _duration_minutes(distance_km: float, speed_kmh: float = AVERAGE_CITY_SPEED_KMH) -> float:
    if speed_kmh <= 0:
        return 0.0
    return (distance_km / speed_kmh) * 60.0


def bearing_degrees(origin: Coordinate, destination: Coordinate) -> float:
    lat1 = radians(origin[0])
    lat2 = radians(destination[0])
    delta_longitude = radians(destination[1] - origin[1])
    x = sin(delta_longitude) * cos(lat2)
    y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(delta_longitude)
    return (degrees(atan2(x, y)) + 360.0) % 360.0


def _angle_delta(first_bearing: float, second_bearing: float) -> float:
    return abs((first_bearing - second_bearing + 180.0) % 360.0 - 180.0)


def angle_between_routes(
    driver_origin: Coordinate,
    driver_destination: Coordinate,
    passenger_pickup: Coordinate,
    passenger_dropoff: Coordinate,
) -> float:
    driver_bearing = bearing_degrees(driver_origin, driver_destination)
    passenger_bearing = bearing_degrees(passenger_pickup, passenger_dropoff)
    return _angle_delta(driver_bearing, passenger_bearing)


def _point_to_segment_projection_km(
    point: Coordinate,
    segment_start: Coordinate,
    segment_end: Coordinate,
) -> tuple[float, float]:
    lat0 = radians((segment_start[0] + segment_end[0] + point[0]) / 3.0)

    def to_xy(coordinate: Coordinate) -> tuple[float, float]:
        x = coordinate[1] * cos(lat0) * 111.320
        y = coordinate[0] * 110.574
        return x, y

    px, py = to_xy(point)
    sx, sy = to_xy(segment_start)
    ex, ey = to_xy(segment_end)
    dx = ex - sx
    dy = ey - sy
    length_squared = dx * dx + dy * dy
    if length_squared == 0:
        return _coordinate_distance_km(point, segment_start), 0.0
    t = max(0.0, min(1.0, ((px - sx) * dx + (py - sy) * dy) / length_squared))
    nearest_x = sx + t * dx
    nearest_y = sy + t * dy
    return sqrt((px - nearest_x) ** 2 + (py - nearest_y) ** 2), t


def point_to_segment_distance_km(point: Coordinate, segment_start: Coordinate, segment_end: Coordinate) -> float:
    distance_km, _ = _point_to_segment_projection_km(point, segment_start, segment_end)
    return distance_km


def _has_route_coordinates(ride_request: RideRequest, trip: Trip) -> bool:
    return all(
        value is not None
        for value in [
            ride_request.origin_latitude,
            ride_request.origin_longitude,
            ride_request.destination_latitude,
            ride_request.destination_longitude,
            trip.origin_latitude,
            trip.origin_longitude,
            trip.destination_latitude,
            trip.destination_longitude,
        ]
    )


def _route_coordinates(ride_request: RideRequest, trip: Trip) -> RouteCoordinates | None:
    if not _has_route_coordinates(ride_request, trip):
        return None
    return RouteCoordinates(
        driver_origin=(trip.origin_latitude, trip.origin_longitude),
        driver_destination=(trip.destination_latitude, trip.destination_longitude),
        passenger_pickup=(ride_request.origin_latitude, ride_request.origin_longitude),
        passenger_dropoff=(ride_request.destination_latitude, ride_request.destination_longitude),
    )


def _present_coordinates(ride_request: RideRequest, trip: Trip) -> list[Coordinate]:
    raw_coordinates = [
        (ride_request.origin_latitude, ride_request.origin_longitude),
        (ride_request.destination_latitude, ride_request.destination_longitude),
        (trip.origin_latitude, trip.origin_longitude),
        (trip.destination_latitude, trip.destination_longitude),
    ]
    return [(latitude, longitude) for latitude, longitude in raw_coordinates if latitude is not None and longitude is not None]


def _within_service_area(coordinate: Coordinate) -> bool:
    distance_from_center = haversine_distance_km(
        coordinate[0],
        coordinate[1],
        settings.service_area_center_latitude,
        settings.service_area_center_longitude,
    )
    return distance_from_center <= settings.service_area_radius_km


def route_detour_km(ride_request: RideRequest, trip: Trip) -> tuple[float, float] | None:
    coordinates = _route_coordinates(ride_request, trip)
    if coordinates is None:
        return None
    insertion = estimate_route_insertion(coordinates)
    return insertion.pickup_walk_distance_km, insertion.dropoff_walk_distance_km


def estimate_route_insertion(coordinates: RouteCoordinates) -> RouteInsertionEstimate:
    original_driver_distance_km = _coordinate_distance_km(coordinates.driver_origin, coordinates.driver_destination)
    shared_route_distance_km = (
        _coordinate_distance_km(coordinates.driver_origin, coordinates.passenger_pickup)
        + _coordinate_distance_km(coordinates.passenger_pickup, coordinates.passenger_dropoff)
        + _coordinate_distance_km(coordinates.passenger_dropoff, coordinates.driver_destination)
    )
    detour_distance_km = max(0.0, shared_route_distance_km - original_driver_distance_km)
    passenger_direct_distance_km = _coordinate_distance_km(coordinates.passenger_pickup, coordinates.passenger_dropoff)
    pickup_walk_distance_km, pickup_route_progress = _point_to_segment_projection_km(
        coordinates.passenger_pickup,
        coordinates.driver_origin,
        coordinates.driver_destination,
    )
    dropoff_walk_distance_km, dropoff_route_progress = _point_to_segment_projection_km(
        coordinates.passenger_dropoff,
        coordinates.driver_origin,
        coordinates.driver_destination,
    )
    route_order_score = calculate_route_order_score(pickup_route_progress, dropoff_route_progress)
    walking_duration_min = _duration_minutes(
        pickup_walk_distance_km + dropoff_walk_distance_km,
        AVERAGE_WALK_SPEED_KMH,
    )
    original_driver_duration_min = _duration_minutes(original_driver_distance_km)
    shared_route_duration_min = _duration_minutes(shared_route_distance_km)
    detour_duration_min = max(0.0, shared_route_duration_min - original_driver_duration_min)
    passenger_direct_duration_min = _duration_minutes(passenger_direct_distance_km)
    angle = angle_between_routes(
        coordinates.driver_origin,
        coordinates.driver_destination,
        coordinates.passenger_pickup,
        coordinates.passenger_dropoff,
    )
    alignment_delay = passenger_direct_duration_min * max(0.0, min(angle, 75.0)) / 75.0 * 0.35
    shared_passenger_duration_min = passenger_direct_duration_min + walking_duration_min + alignment_delay
    return RouteInsertionEstimate(
        original_driver_distance_km=original_driver_distance_km,
        original_driver_duration_min=original_driver_duration_min,
        shared_route_distance_km=shared_route_distance_km,
        shared_route_duration_min=shared_route_duration_min,
        detour_distance_km=detour_distance_km,
        detour_duration_min=detour_duration_min,
        passenger_direct_duration_min=passenger_direct_duration_min,
        shared_passenger_duration_min=shared_passenger_duration_min,
        pickup_walk_distance_km=pickup_walk_distance_km,
        dropoff_walk_distance_km=dropoff_walk_distance_km,
        pickup_route_progress=pickup_route_progress,
        dropoff_route_progress=dropoff_route_progress,
        route_order_score=route_order_score,
    )


def proximity_score(distance_km: float, max_distance_km: float) -> float:
    if distance_km > max_distance_km:
        return 0.0
    return _clamp01(1.0 - distance_km / max_distance_km)


def calculate_route_alignment_score(angle_degrees: float) -> float:
    return _clamp01(1.0 - angle_degrees / 75.0)


def calculate_route_order_score(pickup_progress: float, dropoff_progress: float) -> float:
    progress_delta = dropoff_progress - pickup_progress
    if progress_delta < 0:
        return 0.0
    return _clamp01(0.55 + progress_delta / 0.45)


def route_alignment_score(ride_request: RideRequest, trip: Trip) -> float:
    coordinates = _route_coordinates(ride_request, trip)
    if coordinates is None:
        return min(0.68, (place_score(ride_request.origin, trip.origin) + place_score(ride_request.destination, trip.destination)) / 200)
    angle = angle_between_routes(
        coordinates.driver_origin,
        coordinates.driver_destination,
        coordinates.passenger_pickup,
        coordinates.passenger_dropoff,
    )
    return calculate_route_alignment_score(angle)


def calculate_driver_detour_score(route_insertion: RouteInsertionEstimate) -> float:
    distance_score = proximity_score(route_insertion.detour_distance_km, MAX_DRIVER_DETOUR_KM)
    duration_score = proximity_score(route_insertion.detour_duration_min, MAX_DRIVER_DETOUR_MINUTES)
    return (distance_score + duration_score) / 2


def time_score(preferred_time: datetime, departure_time: datetime) -> float:
    diff_minutes = abs((departure_time - preferred_time).total_seconds()) / 60
    if diff_minutes > MATCH_TIME_WINDOW_MINUTES:
        return 0.0
    return _clamp01(1.0 - diff_minutes / MATCH_TIME_WINDOW_MINUTES)


def capacity_score(ride_request: RideRequest, trip: Trip) -> float:
    if trip.available_seats < ride_request.passenger_count:
        return 0.0
    unused_seats = trip.available_seats - ride_request.passenger_count
    denominator = max(1, trip.total_seats or trip.available_seats)
    return _clamp01(1.0 - unused_seats / denominator)


def driver_rating_score(trip: Trip) -> float:
    driver_rating = max(0.0, min(5.0, trip.driver.rating or 0.0))
    return driver_rating / 5.0


def _passenger_rating_score(ride_request: RideRequest) -> float:
    passenger_rating = max(0.0, min(5.0, ride_request.rider.rating or 0.0))
    return passenger_rating / 5.0


def _passenger_cancellation_count(ride_request: RideRequest) -> int:
    return sum(1 for request in ride_request.rider.ride_requests if request.status == RideRequestStatus.cancelled)


def _passenger_reliability_score(ride_request: RideRequest) -> float:
    cancellation_count = _passenger_cancellation_count(ride_request)
    return _clamp01(1.0 - min(cancellation_count, 5) * 0.12)


def calculate_passenger_convenience_score(
    route_insertion: RouteInsertionEstimate,
    waiting_time_minutes: float,
) -> float:
    pickup_score = proximity_score(route_insertion.pickup_walk_distance_km, MAX_PASSENGER_WALK_KM)
    dropoff_score = proximity_score(route_insertion.dropoff_walk_distance_km, MAX_PASSENGER_WALK_KM)
    waiting_score = proximity_score(waiting_time_minutes, MATCH_TIME_WINDOW_MINUTES)
    if route_insertion.passenger_direct_duration_min <= 0:
        ride_time_score = 1.0
    else:
        ride_ratio = route_insertion.shared_passenger_duration_min / route_insertion.passenger_direct_duration_min
        ride_time_score = _clamp01(1.0 - max(0.0, ride_ratio - 1.0) / 0.75)
    return (
        pickup_score * 0.30
        + dropoff_score * 0.20
        + waiting_score * 0.25
        + ride_time_score * 0.20
        + route_insertion.route_order_score * 0.05
    )


def calculate_driver_acceptance_score(
    ride_request: RideRequest,
    trip: Trip,
    route_insertion: RouteInsertionEstimate,
) -> float:
    detour_score = calculate_driver_detour_score(route_insertion)
    pickup_route_score = proximity_score(route_insertion.pickup_walk_distance_km, MAX_PICKUP_OFFSET_KM)
    dropoff_route_score = proximity_score(route_insertion.dropoff_walk_distance_km, MAX_DROPOFF_OFFSET_KM)
    route_proximity_score = (pickup_route_score + dropoff_route_score) / 2
    return (
        detour_score * 0.35
        + route_proximity_score * 0.20
        + capacity_score(ride_request, trip) * 0.15
        + _passenger_rating_score(ride_request) * 0.15
        + _passenger_reliability_score(ride_request) * 0.10
        + route_insertion.route_order_score * 0.05
    )


def calculate_supply_efficiency_score(
    ride_request: RideRequest,
    trip: Trip,
    route_alignment: float,
    driver_detour: float,
    passenger_convenience: float,
) -> float:
    candidate_quality = (route_alignment + driver_detour + passenger_convenience) / 3
    seats_after_match = trip.available_seats - ride_request.passenger_count
    scarcity_score = 1.0 - max(0, seats_after_match) / max(1, trip.total_seats or trip.available_seats)
    return _clamp01(candidate_quality * 0.75 + scarcity_score * 0.25)


def _trust_safety_score(ride_request: RideRequest, trip: Trip) -> float:
    return (
        _passenger_rating_score(ride_request) * 0.35
        + _passenger_reliability_score(ride_request) * 0.35
        + driver_rating_score(trip) * 0.30
    )


def calculate_final_match_score(score_breakdown: dict[str, float]) -> float:
    weighted_sum = 0.0
    total_weight = 0.0
    for key, weight in MATCH_SCORE_WEIGHTS.items():
        breakdown_key = f"{key}_score"
        weighted_sum += score_breakdown.get(breakdown_key, 0.0) * weight
        total_weight += weight
    if total_weight <= 0:
        return 0.0
    return round((weighted_sum / total_weight) * 100, 2)


def build_match_explanation(
    ride_request: RideRequest,
    route_insertion: RouteInsertionEstimate | None,
    score_breakdown: dict[str, float],
    angle_degrees: float | None,
    waiting_time_minutes: float,
    used_coordinate_algorithm: bool,
) -> list[str]:
    reasons: list[str] = []
    if used_coordinate_algorithm and angle_degrees is not None:
        if angle_degrees <= 20:
            reasons.append("Passenger route is strongly aligned with driver route")
        elif angle_degrees <= 45:
            reasons.append("Passenger route is aligned with driver route")
        else:
            reasons.append("Passenger route is only weakly aligned, but still feasible")
    else:
        reasons.append("Location labels matched using fallback text scoring because route coordinates are incomplete")

    if route_insertion is not None:
        reasons.append(f"Estimated driver detour is {round(route_insertion.detour_duration_min)} minutes")
        if route_insertion.route_order_score >= 0.9:
            reasons.append("Pickup appears before dropoff along the driver's route")
        if route_insertion.pickup_walk_distance_km <= 0.5:
            reasons.append("Pickup is near the driver's route")
        if route_insertion.dropoff_walk_distance_km <= 0.5:
            reasons.append("Dropoff is near the driver's route")
    reasons.append(f"Departure time difference is {round(waiting_time_minutes)} minutes")
    if score_breakdown["driver_acceptance_score"] >= 0.75:
        reasons.append("Driver acceptance probability is high for this request")
    if score_breakdown["trust_safety_score"] >= 0.85:
        reasons.append("Passenger has a good reliability profile")
    return reasons[:6]


def _fallback_match_evaluation(ride_request: RideRequest, trip: Trip) -> MatchEvaluation:
    route_alignment = route_alignment_score(ride_request, trip)
    waiting_time_minutes = abs((trip.departure_time - ride_request.preferred_time).total_seconds()) / 60
    time_fit = time_score(ride_request.preferred_time, trip.departure_time)
    driver_detour = min(0.68, route_alignment)
    passenger_convenience = min(0.72, (route_alignment * 0.60 + time_fit * 0.40))
    driver_acceptance = min(
        0.72,
        route_alignment * 0.35
        + capacity_score(ride_request, trip) * 0.20
        + _passenger_rating_score(ride_request) * 0.25
        + _passenger_reliability_score(ride_request) * 0.20,
    )
    supply_efficiency = calculate_supply_efficiency_score(
        ride_request,
        trip,
        route_alignment,
        driver_detour,
        passenger_convenience,
    )
    trust_safety = _trust_safety_score(ride_request, trip)
    score_breakdown = {
        "route_alignment_score": route_alignment,
        "driver_detour_score": driver_detour,
        "passenger_convenience_score": passenger_convenience,
        "time_fit_score": time_fit,
        "driver_acceptance_score": driver_acceptance,
        "supply_efficiency_score": supply_efficiency,
        "trust_safety_score": trust_safety,
    }
    final_score = calculate_final_match_score(score_breakdown)
    reasons = build_match_explanation(
        ride_request,
        None,
        score_breakdown,
        None,
        waiting_time_minutes,
        used_coordinate_algorithm=False,
    )
    if final_score < MIN_MATCH_SCORE:
        return MatchEvaluation(final_score, _rounded_breakdown(score_breakdown), reasons, "below_minimum_score")
    return MatchEvaluation(final_score, _rounded_breakdown(score_breakdown), reasons)


def _rounded_breakdown(score_breakdown: dict[str, float]) -> dict[str, float]:
    return {key: round(value, 2) for key, value in score_breakdown.items()}


def evaluate_match_candidate(ride_request: RideRequest, trip: Trip) -> MatchEvaluation:
    reject_reason = hard_constraint_reject_reason(ride_request, trip)
    if reject_reason is not None:
        return MatchEvaluation(0.0, {}, [], reject_reason)

    coordinates = _route_coordinates(ride_request, trip)
    if coordinates is None:
        return _fallback_match_evaluation(ride_request, trip)

    angle_degrees = angle_between_routes(
        coordinates.driver_origin,
        coordinates.driver_destination,
        coordinates.passenger_pickup,
        coordinates.passenger_dropoff,
    )
    if angle_degrees > 90:
        return MatchEvaluation(0.0, {}, [], "opposite_direction")

    route_insertion = estimate_route_insertion(coordinates)
    if route_insertion.route_order_score <= 0:
        return MatchEvaluation(0.0, {}, [], "route_sequence_reversed", route_insertion)
    if route_insertion.detour_distance_km > MAX_DRIVER_DETOUR_KM:
        return MatchEvaluation(0.0, {}, [], "too_much_driver_detour")
    if route_insertion.detour_duration_min > MAX_DRIVER_DETOUR_MINUTES:
        return MatchEvaluation(0.0, {}, [], "too_much_driver_detour")
    if (
        route_insertion.pickup_walk_distance_km > MAX_PASSENGER_WALK_KM
        or route_insertion.dropoff_walk_distance_km > MAX_PASSENGER_WALK_KM
    ):
        return MatchEvaluation(0.0, {}, [], "passenger_walk_too_far")

    waiting_time_minutes = abs((trip.departure_time - ride_request.preferred_time).total_seconds()) / 60
    route_alignment = calculate_route_alignment_score(angle_degrees) * (0.75 + route_insertion.route_order_score * 0.25)
    driver_detour = calculate_driver_detour_score(route_insertion)
    passenger_convenience = calculate_passenger_convenience_score(route_insertion, waiting_time_minutes)
    driver_acceptance = calculate_driver_acceptance_score(ride_request, trip, route_insertion)
    supply_efficiency = calculate_supply_efficiency_score(
        ride_request,
        trip,
        route_alignment,
        driver_detour,
        passenger_convenience,
    )
    trust_safety = _trust_safety_score(ride_request, trip)
    score_breakdown = {
        "route_alignment_score": route_alignment,
        "route_order_score": route_insertion.route_order_score,
        "driver_detour_score": driver_detour,
        "passenger_convenience_score": passenger_convenience,
        "time_fit_score": time_score(ride_request.preferred_time, trip.departure_time),
        "driver_acceptance_score": driver_acceptance,
        "supply_efficiency_score": supply_efficiency,
        "trust_safety_score": trust_safety,
    }
    final_score = calculate_final_match_score(score_breakdown)
    reasons = build_match_explanation(
        ride_request,
        route_insertion,
        score_breakdown,
        angle_degrees,
        waiting_time_minutes,
        used_coordinate_algorithm=True,
    )
    if final_score < MIN_MATCH_SCORE:
        return MatchEvaluation(
            final_score,
            _rounded_breakdown(score_breakdown),
            reasons,
            "below_minimum_score",
            route_insertion,
        )
    return MatchEvaluation(final_score, _rounded_breakdown(score_breakdown), reasons, None, route_insertion)


def hard_constraint_reject_reason(ride_request: RideRequest, trip: Trip) -> str | None:
    if trip.status not in {TripStatus.posted, TripStatus.matched}:
        return "trip_not_matchable"
    if ride_request.status != RideRequestStatus.pending:
        return "request_not_pending"
    if trip.available_seats < ride_request.passenger_count:
        return "no_seats"
    if trip.driver_id == ride_request.rider_id:
        return "same_driver_and_passenger"
    if time_score(ride_request.preferred_time, trip.departure_time) <= 0:
        return "time_window_not_overlap"
    if ride_request.gender_preference == GenderPreference.same_gender and trip.driver.gender != ride_request.rider.gender:
        return "gender_preference_mismatch"
    for coordinate in _present_coordinates(ride_request, trip):
        if not _within_service_area(coordinate):
            return "outside_service_area"
    return None


def is_hard_match(ride_request: RideRequest, trip: Trip) -> bool:
    return hard_constraint_reject_reason(ride_request, trip) is None


def calculate_match_score(ride_request: RideRequest, trip: Trip) -> float:
    evaluation = evaluate_match_candidate(ride_request, trip)
    if evaluation.reject_reason is not None:
        return 0.0
    return evaluation.final_score


def _upsert_recommendation(
    db: Session,
    ride_request: RideRequest,
    trip: Trip,
    evaluation: MatchEvaluation,
) -> RideMatch:
    match = (
        db.query(RideMatch)
        .filter(
            RideMatch.request_id == ride_request.request_id,
            RideMatch.trip_id == trip.trip_id,
        )
        .first()
    )
    if match is None:
        match = RideMatch(
            trip_id=trip.trip_id,
            request_id=ride_request.request_id,
            rider_id=ride_request.rider_id,
            match_score=evaluation.final_score,
            score_breakdown=evaluation.score_breakdown,
            reasons=evaluation.reasons,
            status=MatchStatus.recommended,
        )
    elif match.status == MatchStatus.recommended:
        match.match_score = evaluation.final_score
        match.score_breakdown = evaluation.score_breakdown
        match.reasons = evaluation.reasons
    db.add(match)
    return match


def recommend_trips_for_request(db: Session, ride_request: RideRequest) -> list[RideMatch]:
    candidate_trips = (
        db.query(Trip)
        .join(User, Trip.driver_id == User.user_id)
        .filter(Trip.status.in_([TripStatus.posted, TripStatus.matched]))
        .all()
    )
    scored: list[tuple[float, RideMatch]] = []
    for trip in candidate_trips:
        evaluation = evaluate_match_candidate(ride_request, trip)
        if evaluation.reject_reason is not None:
            continue
        scored.append((evaluation.final_score, _upsert_recommendation(db, ride_request, trip, evaluation)))

    db.commit()
    matches = [match for _, match in sorted(scored, key=lambda item: item[0], reverse=True)[:5]]
    for match in matches:
        db.refresh(match)
    return matches


def recommend_requests_for_trip(db: Session, trip: Trip) -> list[RideMatch]:
    candidate_requests = db.query(RideRequest).filter(RideRequest.status == RideRequestStatus.pending).all()
    scored: list[tuple[float, RideMatch]] = []
    for ride_request in candidate_requests:
        evaluation = evaluate_match_candidate(ride_request, trip)
        if evaluation.reject_reason is not None:
            continue
        scored.append((evaluation.final_score, _upsert_recommendation(db, ride_request, trip, evaluation)))

    db.commit()
    matches = [match for _, match in sorted(scored, key=lambda item: item[0], reverse=True)[:5]]
    for match in matches:
        db.refresh(match)
    return matches
