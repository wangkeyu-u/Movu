from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PaymentMethod, PaymentStatus


class PaymentSimulationRequest(BaseModel):
    distance_km: float | None = Field(default=None, ge=0)


class PaymentRead(BaseModel):
    payment_id: int
    match_id: int
    payer_id: int
    amount: float
    payment_status: PaymentStatus
    payment_method: PaymentMethod
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentSimulationResponse(BaseModel):
    payment: PaymentRead
    base_fare: float
    rate_per_km: float
    distance_km: float
    passenger_count: int
    total_fare: float
    fare_per_passenger: float
