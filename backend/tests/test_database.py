from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.app.database import TelemetryStore
from backend.app.risk_engine import classify_risk


class TelemetryStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        database_path = str(Path(self.temp_directory.name) / "test.db")
        self.store = TelemetryStore(database_path)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_record_and_read_latest_telemetry(self) -> None:
        data = {
            "device_id": "TDP-001",
            "timestamp": "2026-08-21T10:00:00+07:00",
            "distance_front_cm": 40,
            "battery_percent": 80,
            "tilt_degree": 5,
            "emergency_button": False,
        }
        decision = classify_risk(data)
        self.store.record(data, decision, "2026-08-21T03:00:01+00:00")

        latest = self.store.latest("TDP-001")
        self.assertIsNotNone(latest)
        assert latest is not None
        self.assertEqual(latest["device_id"], "TDP-001")

        events = self.store.events("TDP-001")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["risk_status"], "DANGER")


if __name__ == "__main__":
    unittest.main()

