"""SQLite persistence for telemetry and risk events."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Mapping

from .risk_engine import RiskDecision, RiskStatus


SCHEMA = """
CREATE TABLE IF NOT EXISTS sensor_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    source_timestamp TEXT NOT NULL,
    received_at TEXT NOT NULL,
    distance_front_cm REAL NOT NULL,
    distance_side_cm REAL,
    tilt_degree REAL NOT NULL DEFAULT 0,
    battery_percent REAL NOT NULL,
    emergency_button INTEGER NOT NULL DEFAULT 0,
    gps_lat REAL,
    gps_lng REAL,
    payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sensor_logs_device_received
ON sensor_logs(device_id, received_at DESC);

CREATE TABLE IF NOT EXISTS risk_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_log_id INTEGER NOT NULL,
    device_id TEXT NOT NULL,
    risk_status TEXT NOT NULL,
    reasons_json TEXT NOT NULL,
    priority INTEGER NOT NULL,
    notified INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY(sensor_log_id) REFERENCES sensor_logs(id)
);

CREATE INDEX IF NOT EXISTS idx_risk_events_device_created
ON risk_events(device_id, created_at DESC);
"""


class TelemetryStore:
    def __init__(self, database_path: str) -> None:
        self.database_path = database_path
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(SCHEMA)

    def record(
        self,
        payload: Mapping[str, Any],
        decision: RiskDecision,
        received_at: str,
    ) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO sensor_logs (
                    device_id, source_timestamp, received_at,
                    distance_front_cm, distance_side_cm, tilt_degree,
                    battery_percent, emergency_button, gps_lat, gps_lng,
                    payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(payload["device_id"]),
                    str(payload["timestamp"]),
                    received_at,
                    float(payload["distance_front_cm"]),
                    payload.get("distance_side_cm"),
                    float(payload.get("tilt_degree", 0)),
                    float(payload["battery_percent"]),
                    int(bool(payload.get("emergency_button", False))),
                    payload.get("gps_lat"),
                    payload.get("gps_lng"),
                    json.dumps(dict(payload), ensure_ascii=False),
                ),
            )
            sensor_log_id = int(cursor.lastrowid)

            if decision.status is not RiskStatus.SAFE:
                connection.execute(
                    """
                    INSERT INTO risk_events (
                        sensor_log_id, device_id, risk_status,
                        reasons_json, priority, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        sensor_log_id,
                        str(payload["device_id"]),
                        decision.status.value,
                        json.dumps(list(decision.reasons), ensure_ascii=False),
                        decision.priority,
                        received_at,
                    ),
                )
            return sensor_log_id

    def latest(self, device_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM sensor_logs
                WHERE device_id = ?
                ORDER BY received_at DESC, id DESC
                LIMIT 1
                """,
                (device_id,),
            ).fetchone()
        return dict(row) if row else None

    def events(self, device_id: str, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM risk_events
                WHERE device_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (device_id, min(max(limit, 1), 200)),
            ).fetchall()

        result: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["reasons"] = json.loads(item.pop("reasons_json"))
            result.append(item)
        return result

