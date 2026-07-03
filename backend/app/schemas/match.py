from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import MatchStatus


class MatchRead(BaseModel):
    match_id: int
    trip_id: int
    request_id: int
    rider_id: int
    match_score: float
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)
    status: MatchStatus
    created_at: datetime

    @field_validator("score_breakdown", mode="before")
    @classmethod
    def default_score_breakdown(cls, value: dict[str, float] | None) -> dict[str, float]:
        return value or {}

    @field_validator("reasons", mode="before")
    @classmethod
    def default_reasons(cls, value: list[str] | None) -> list[str]:
        return value or []

    model_config = ConfigDict(from_attributes=True)
