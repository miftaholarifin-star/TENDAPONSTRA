"""Pydantic request and response models for the REST API."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class TelemetryPayload(BaseModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    device_id: str = Field(min_length=1, max_length=100)
    timestamp: datetime
    distance_front_cm: float = Field(ge=0)
    distance_side_cm: float | None = Field(default=None, ge=0)
    tilt_degree: float = Field(default=0, ge=-180, le=180)
    battery_percent: float = Field(ge=0, le=100)
    emergency_button: bool = False
    gps_lat: float | None = Field(default=None, ge=-90, le=90)
    gps_lng: float | None = Field(default=None, ge=-180, le=180)

    def to_engine_dict(self) -> dict[str, object]:
        data = self.model_dump(mode="json")
        data["timestamp"] = self.timestamp.isoformat()
        return data


class TelemetryResponse(BaseModel):
    device_id: str
    received_at: datetime
    risk_status: str
    reasons: list[str]
    priority: int


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

