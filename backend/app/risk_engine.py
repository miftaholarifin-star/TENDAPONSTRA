"""Risk classification engine for TENDAPONSTRA telemetry."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Mapping


class RiskStatus(str, Enum):
    SAFE = "SAFE"
    WARNING = "WARNING"
    DANGER = "DANGER"


@dataclass(frozen=True)
class RiskThresholds:
    safe_distance_cm: float = 100.0
    danger_distance_cm: float = 50.0
    low_battery_percent: float = 30.0
    max_tilt_degree: float = 60.0

    def __post_init__(self) -> None:
        if self.danger_distance_cm <= 0:
            raise ValueError("danger_distance_cm harus lebih besar dari nol")
        if self.safe_distance_cm <= self.danger_distance_cm:
            raise ValueError(
                "safe_distance_cm harus lebih besar dari danger_distance_cm"
            )
        if not 0 <= self.low_battery_percent <= 100:
            raise ValueError("low_battery_percent harus berada pada rentang 0-100")
        if not 0 < self.max_tilt_degree <= 180:
            raise ValueError("max_tilt_degree harus berada pada rentang 0-180")


@dataclass(frozen=True)
class RiskDecision:
    status: RiskStatus
    reasons: tuple[str, ...]
    priority: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "risk_status": self.status.value,
            "reasons": list(self.reasons),
            "priority": self.priority,
        }


REQUIRED_FIELDS = (
    "device_id",
    "timestamp",
    "distance_front_cm",
    "battery_percent",
)


def _number(data: Mapping[str, Any], key: str, default: float | None = None) -> float:
    value = data.get(key, default)
    if value is None:
        raise ValueError(f"Field {key} wajib diisi")
    if isinstance(value, bool):
        raise ValueError(f"Field {key} harus berupa angka")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Field {key} harus berupa angka") from exc


def validate_payload(data: Mapping[str, Any]) -> None:
    """Validate required telemetry fields and operational ranges."""

    missing = [key for key in REQUIRED_FIELDS if data.get(key) in (None, "")]
    if missing:
        raise ValueError(f"Field wajib tidak ditemukan: {', '.join(missing)}")

    if not str(data["device_id"]).strip():
        raise ValueError("device_id tidak boleh kosong")

    timestamp = str(data["timestamp"]).replace("Z", "+00:00")
    try:
        datetime.fromisoformat(timestamp)
    except ValueError as exc:
        raise ValueError("timestamp harus menggunakan format ISO 8601") from exc

    distance = _number(data, "distance_front_cm")
    battery = _number(data, "battery_percent")
    tilt = abs(_number(data, "tilt_degree", 0.0))

    if distance < 0:
        raise ValueError("distance_front_cm tidak boleh negatif")
    if not 0 <= battery <= 100:
        raise ValueError("battery_percent harus berada pada rentang 0-100")
    if tilt > 180:
        raise ValueError("tilt_degree harus berada pada rentang -180 sampai 180")


def classify_risk(
    data: Mapping[str, Any], thresholds: RiskThresholds | None = None
) -> RiskDecision:
    """Classify risk using deterministic priority and override rules."""

    validate_payload(data)
    active = thresholds or RiskThresholds()

    emergency = bool(data.get("emergency_button", False))
    distance = _number(data, "distance_front_cm")
    battery = _number(data, "battery_percent")
    tilt = abs(_number(data, "tilt_degree", 0.0))

    if emergency:
        return RiskDecision(
            RiskStatus.DANGER,
            ("Tombol darurat aktif. Respons segera diperlukan.",),
            1,
        )

    if distance < active.danger_distance_cm:
        return RiskDecision(
            RiskStatus.DANGER,
            (f"Halangan sangat dekat: {distance:.1f} cm",),
            2,
        )

    if tilt >= active.max_tilt_degree:
        return RiskDecision(
            RiskStatus.DANGER,
            (f"Kemiringan ekstrem: {tilt:.1f} derajat",),
            3,
        )

    warnings: list[str] = []
    if distance <= active.safe_distance_cm:
        warnings.append(f"Halangan terdeteksi: {distance:.1f} cm")
    if battery < active.low_battery_percent:
        warnings.append(f"Baterai rendah: {battery:.1f} persen")

    if warnings:
        return RiskDecision(RiskStatus.WARNING, tuple(warnings), 4)

    return RiskDecision(
        RiskStatus.SAFE,
        ("Kondisi normal. Tidak ada risiko terdeteksi.",),
        6,
    )

