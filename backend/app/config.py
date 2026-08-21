"""Runtime configuration for TENDAPONSTRA."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} harus berupa angka, menerima: {raw_value!r}") from exc


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    database_path: str = os.getenv(
        "TENDAPONSTRA_DATABASE_PATH", "data/tendaponstra.db"
    )
    safe_distance_cm: float = _float_env(
        "TENDAPONSTRA_SAFE_DISTANCE_CM", 100.0
    )
    danger_distance_cm: float = _float_env(
        "TENDAPONSTRA_DANGER_DISTANCE_CM", 50.0
    )
    low_battery_percent: float = _float_env(
        "TENDAPONSTRA_LOW_BATTERY_PERCENT", 30.0
    )
    max_tilt_degree: float = _float_env(
        "TENDAPONSTRA_MAX_TILT_DEGREE", 60.0
    )
    allowed_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv(
            "TENDAPONSTRA_ALLOWED_ORIGINS",
            "http://127.0.0.1:5500,http://localhost:5500",
        ).split(",")
        if origin.strip()
    )


settings = Settings()

