from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import GenderPreference, RideRequestStatus


class RideRequestCreate(BaseModel):
    origin: str = Field(min_length=2, max_length=255)
    destination: str = Field(min_length=2, max_length=255)
    origin_latitude: float | None = Field(default=None, ge=-90, le=90)
    origin_longitude: float | None = Field(default=None, ge=-180, le=180)
    destination_latitude: float | None = Field(default=None, ge=-90, le=90)
    destination_longitude: float | None = Field(default=None, ge=-180, le=180)
    preferred_time: datetime
    preferred_time_timezone: str = Field(default="Asia/Kuala_Lumpur", min_length=1, max_length=64)
    passenger_count: int = Field(ge=1, le=6)
    gender_preference: GenderPreference = GenderPreference.none
    distance_km: float | None = Field(default=None, ge=0)


class RideRequestRead(BaseModel):
    request_id: int
    rider_id: int
    origin: str
    destination: str
    origin_latitude: float | None
    origin_longitude: float | None
    destination_latitude: float | None
    destination_longitude: float | None
    preferred_time: datetime
    preferred_time_timezone: str
    passenger_count: int
    gender_preference: GenderPreference
    distance_km: float | None
    status: RideRequestStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
