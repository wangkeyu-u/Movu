from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import TripStatus


class TripCreate(BaseModel):
    origin: str = Field(min_length=2, max_length=255)
    destination: str = Field(min_length=2, max_length=255)
    origin_latitude: float | None = Field(default=None, ge=-90, le=90)
    origin_longitude: float | None = Field(default=None, ge=-180, le=180)
    destination_latitude: float | None = Field(default=None, ge=-90, le=90)
    destination_longitude: float | None = Field(default=None, ge=-180, le=180)
    departure_time: datetime
    available_seats: int = Field(ge=1, le=8)


class TripStatusUpdate(BaseModel):
    status: TripStatus

    @field_validator("status")
    @classmethod
    def validate_driver_status(cls, value: TripStatus) -> TripStatus:
        if value == TripStatus.full:
            raise ValueError("Full status is set automatically when seats become zero")
        return value


class TripRead(BaseModel):
    trip_id: int
    driver_id: int
    origin: str
    destination: str
    origin_latitude: float | None
    origin_longitude: float | None
    destination_latitude: float | None
    destination_longitude: float | None
    departure_time: datetime
    available_seats: int
    total_seats: int
    status: TripStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
