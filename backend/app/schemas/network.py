from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TripStatus, VerificationStatus


class NetworkUserRead(BaseModel):
    user_id: int
    name: str
    role: str
    rating: float


class NetworkVehicleRead(BaseModel):
    vehicle_id: int
    plate_number: str
    vehicle_model: str
    seat_count: int
    verification_status: VerificationStatus


class NetworkRiderRead(BaseModel):
    user_id: int
    name: str
    rating: float
    passenger_count: int
    pickup: str
    dropoff: str


class TripNetworkRead(BaseModel):
    trip_id: int
    driver_id: int
    origin: str
    destination: str
    origin_latitude: float | None
    origin_longitude: float | None
    destination_latitude: float | None
    destination_longitude: float | None
    departure_time: datetime
    departure_time_timezone: str
    available_seats: int
    total_seats: int
    status: TripStatus
    created_at: datetime
    driver: NetworkUserRead
    vehicle: NetworkVehicleRead | None
    riders: list[NetworkRiderRead]


class TripMessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=600)


class TripMessageRead(BaseModel):
    message_id: int
    trip_id: int
    sender_id: int
    sender_name: str
    sender_role: str
    body: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
