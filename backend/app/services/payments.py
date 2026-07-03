from dataclasses import dataclass


BASE_FARE_RM = 3.0
RATE_PER_KM_RM = 1.2


@dataclass(frozen=True)
class FareBreakdown:
    base_fare: float
    rate_per_km: float
    distance_km: float
    passenger_count: int
    total_fare: float
    fare_per_passenger: float


def calculate_fare(distance_km: float, passenger_count: int) -> FareBreakdown:
    if distance_km < 0:
        raise ValueError("Distance cannot be negative")
    if passenger_count <= 0:
        raise ValueError("Passenger count must be greater than zero")

    total_fare = BASE_FARE_RM + distance_km * RATE_PER_KM_RM
    fare_per_passenger = total_fare / passenger_count
    return FareBreakdown(
        base_fare=BASE_FARE_RM,
        rate_per_km=RATE_PER_KM_RM,
        distance_km=round(distance_km, 2),
        passenger_count=passenger_count,
        total_fare=round(total_fare, 2),
        fare_per_passenger=round(fare_per_passenger, 2),
    )
