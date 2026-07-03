from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import SOSStatus


class SOSCreate(BaseModel):
    trip_id: int
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class SOSStatusUpdate(BaseModel):
    status: SOSStatus

    @field_validator("status")
    @classmethod
    def validate_admin_status(cls, value: SOSStatus) -> SOSStatus:
        if value == SOSStatus.new:
            raise ValueError("Admin can update SOS to reviewing, resolved, or false_alarm")
        return value


class SOSRead(BaseModel):
    sos_id: int
    user_id: int
    trip_id: int
    latitude: float
    longitude: float
    status: SOSStatus
    triggered_time: datetime
    resolved_time: datetime | None

    model_config = ConfigDict(from_attributes=True)
