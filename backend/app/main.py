"""FastAPI application for TENDAPONSTRA."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config import settings
from .database import TelemetryStore
from .models import HealthResponse, TelemetryPayload, TelemetryResponse
from .risk_engine import RiskThresholds, classify_risk


app = FastAPI(
    title="TENDAPONSTRA API",
    description=(
        "API pemantauan mobilitas berbasis telemetri IoT dan klasifikasi "
        "risiko real-time."
    ),
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

thresholds = RiskThresholds(
    safe_distance_cm=settings.safe_distance_cm,
    danger_distance_cm=settings.danger_distance_cm,
    low_battery_percent=settings.low_battery_percent,
    max_tilt_degree=settings.max_tilt_degree,
)
store = TelemetryStore(settings.database_path)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="TENDAPONSTRA API",
        version=__version__,
    )


@app.get("/api/v1/thresholds", tags=["configuration"])
def get_thresholds() -> dict[str, float]:
    return {
        "safe_distance_cm": thresholds.safe_distance_cm,
        "danger_distance_cm": thresholds.danger_distance_cm,
        "low_battery_percent": thresholds.low_battery_percent,
        "max_tilt_degree": thresholds.max_tilt_degree,
    }


@app.post(
    "/api/v1/telemetry",
    response_model=TelemetryResponse,
    tags=["telemetry"],
)
def receive_telemetry(payload: TelemetryPayload) -> TelemetryResponse:
    engine_payload = payload.to_engine_dict()
    try:
        decision = classify_risk(engine_payload, thresholds)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    received_at = datetime.now(timezone.utc)
    store.record(engine_payload, decision, received_at.isoformat())

    return TelemetryResponse(
        device_id=payload.device_id,
        received_at=received_at,
        risk_status=decision.status.value,
        reasons=list(decision.reasons),
        priority=decision.priority,
    )


@app.get("/api/v1/devices/{device_id}/latest", tags=["monitoring"])
def latest_telemetry(device_id: str) -> dict[str, object]:
    item = store.latest(device_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Data perangkat belum tersedia")
    return item


@app.get("/api/v1/devices/{device_id}/events", tags=["monitoring"])
def risk_events(
    device_id: str,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, object]]:
    return store.events(device_id, limit)

