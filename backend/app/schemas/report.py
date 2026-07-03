from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import ReportType


class RatingCreate(BaseModel):
    to_user_id: int
    trip_id: int
    score: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class ReportCreate(BaseModel):
    to_user_id: int
    trip_id: int
    report_type: ReportType
    comment: str | None = Field(default=None, max_length=1000)
    score: int | None = Field(default=None, ge=1, le=5)

    @model_validator(mode="after")
    def validate_report_content(self) -> "ReportCreate":
        if self.report_type == ReportType.other and not self.comment:
            raise ValueError("Comment is required for other report type")
        return self


class RatingReportRead(BaseModel):
    record_id: int
    from_user_id: int
    to_user_id: int
    trip_id: int
    score: int | None
    report_type: ReportType | None
    comment: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
