from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LocationCreate(BaseModel):
    trip_id: int
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class LocationRead(BaseModel):
    log_id: int
    trip_id: int
    user_id: int
    latitude: float
    longitude: float
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class LocationMessage(BaseModel):
    trip_id: int
    user_id: int
    latitude: float
    longitude: float
    timestamp: datetime
