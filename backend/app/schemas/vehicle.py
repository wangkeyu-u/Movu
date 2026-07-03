from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import VerificationStatus


class VehicleCreate(BaseModel):
    plate_number: str = Field(min_length=2, max_length=30)
    vehicle_model: str = Field(min_length=2, max_length=120)
    seat_count: int = Field(ge=1, le=8)

    @field_validator("plate_number")
    @classmethod
    def normalize_plate_number(cls, value: str) -> str:
        return value.upper().replace(" ", "")


class VehicleRead(BaseModel):
    vehicle_id: int
    driver_id: int
    plate_number: str
    vehicle_model: str
    seat_count: int
    verification_status: VerificationStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VehicleVerificationUpdate(BaseModel):
    verification_status: VerificationStatus

    @field_validator("verification_status")
    @classmethod
    def validate_admin_status(cls, value: VerificationStatus) -> VerificationStatus:
        if value == VerificationStatus.pending:
            raise ValueError("Vehicle verification can only be approved or rejected by admin")
        return value
