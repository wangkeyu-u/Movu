import math

import httpx
from fastapi import HTTPException, status

from app.core.config import settings


def has_coordinates(
    origin_latitude: float | None,
    origin_longitude: float | None,
    destination_latitude: float | None,
    destination_longitude: float | None,
) -> bool:
    return None not in (
        origin_latitude,
        origin_longitude,
        destination_latitude,
        destination_longitude,
    )


def has_any_coordinate(*coordinates: float | None) -> bool:
    return any(coordinate is not None for coordinate in coordinates)


def haversine_distance_km(
    origin_latitude: float,
    origin_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
) -> float:
    radius_km = 6371.0
    lat1 = math.radians(origin_latitude)
    lat2 = math.radians(destination_latitude)
    delta_lat = math.radians(destination_latitude - origin_latitude)
    delta_lng = math.radians(destination_longitude - origin_longitude)
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lng / 2) ** 2
    )
    return round(2 * radius_km * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)


def distance_from_service_center_km(latitude: float, longitude: float) -> float:
    return haversine_distance_km(
        settings.service_area_center_latitude,
        settings.service_area_center_longitude,
        latitude,
        longitude,
    )


def validate_point_inside_service_area(latitude: float, longitude: float, label: str) -> None:
    distance_km = distance_from_service_center_km(latitude, longitude)
    if distance_km > settings.service_area_radius_km:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label} is outside the Taylor's University {settings.service_area_radius_km:g}km service area",
        )


def validate_route_inside_service_area(
    *,
    origin_latitude: float | None,
    origin_longitude: float | None,
    destination_latitude: float | None,
    destination_longitude: float | None,
    require_coordinates: bool = False,
) -> bool:
    coordinate_values = (
        origin_latitude,
        origin_longitude,
        destination_latitude,
        destination_longitude,
    )
    coordinates_present = has_coordinates(*coordinate_values)
    if not coordinates_present:
        if require_coordinates or has_any_coordinate(*coordinate_values):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Origin and destination coordinates are required",
            )
        return False

    validate_point_inside_service_area(origin_latitude, origin_longitude, "Origin")
    validate_point_inside_service_area(destination_latitude, destination_longitude, "Destination")
    return True


def calculate_route_distance_km(
    *,
    origin_latitude: float,
    origin_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
) -> float:
    url = (
        f"{settings.osrm_base_url.rstrip('/')}/route/v1/driving/"
        f"{origin_longitude},{origin_latitude};{destination_longitude},{destination_latitude}"
    )
    try:
        with httpx.Client(timeout=8) as client:
            response = client.get(url, params={"overview": "false"})
            response.raise_for_status()
            payload = response.json()
            distance_meters = payload["routes"][0]["distance"]
            return round(float(distance_meters) / 1000, 2)
    except Exception as exc:
        if settings.environment == "production":
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Route distance provider unavailable",
            ) from exc
        return haversine_distance_km(
            origin_latitude,
            origin_longitude,
            destination_latitude,
            destination_longitude,
        )
