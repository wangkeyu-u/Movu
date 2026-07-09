from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MovU Carpooling API"
    environment: Literal["development", "test", "staging", "production", "docker"] = "development"
    api_prefix: str = "/api"

    database_url: str = Field(
        default="mysql+pymysql://movu:movu_password@localhost:3306/movu_carpooling",
        description="SQLAlchemy database URL.",
    )

    jwt_secret_key: str = "change-this-secret-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    email_verification_expire_minutes: int = 60 * 24
    frontend_base_url: str = "http://localhost:5174"

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool = True
    osrm_base_url: str = "https://router.project-osrm.org"
    service_area_center_latitude: float = 3.0646454
    service_area_center_longitude: float = 101.6159384
    service_area_radius_km: float = 30.0
    max_driver_detour_km: float = 4.0
    max_driver_detour_minutes: float = 12.0
    max_passenger_walk_km: float = 1.5
    max_pickup_offset_km: float = 3.0
    max_dropoff_offset_km: float = 3.0
    match_time_window_minutes: int = 30
    min_match_score: float = 65.0
    match_score_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "route_alignment": 0.25,
            "driver_detour": 0.20,
            "passenger_convenience": 0.20,
            "time_fit": 0.15,
            "driver_acceptance": 0.10,
            "supply_efficiency": 0.05,
            "trust_safety": 0.05,
        }
    )
    rate_limit_requests: int = 600
    rate_limit_window_seconds: int = 60
    redis_url: str | None = None

    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
    ]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.environment == "production":
            if self.jwt_secret_key == "change-this-secret-in-production":
                raise ValueError("JWT_SECRET_KEY must be set to a strong secret in production")
            if len(self.jwt_secret_key) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")
            if self.database_url.startswith("sqlite"):
                raise ValueError("Production must use MySQL, not SQLite")
            if not self.cors_origins:
                raise ValueError("CORS_ORIGINS must include the production frontend origin")
            if not self.smtp_host or not self.smtp_from_email:
                raise ValueError("SMTP_HOST and SMTP_FROM_EMAIL are required in production")
            if not self.osrm_base_url:
                raise ValueError("OSRM_BASE_URL is required in production")
        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
