from __future__ import annotations

import unittest

from backend.app.risk_engine import RiskStatus, classify_risk, validate_payload


def payload(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "device_id": "TDP-001",
        "timestamp": "2026-08-21T10:00:00+07:00",
        "distance_front_cm": 150,
        "battery_percent": 80,
        "tilt_degree": 5,
        "emergency_button": False,
    }
    data.update(overrides)
    return data


class RiskEngineTests(unittest.TestCase):
    def test_safe_condition(self) -> None:
        decision = classify_risk(payload())
        self.assertEqual(decision.status, RiskStatus.SAFE)

    def test_close_obstacle_is_danger(self) -> None:
        decision = classify_risk(payload(distance_front_cm=40))
        self.assertEqual(decision.status, RiskStatus.DANGER)
        self.assertEqual(decision.priority, 2)

    def test_emergency_button_overrides_other_values(self) -> None:
        decision = classify_risk(
            payload(
                emergency_button=True,
                distance_front_cm=150,
                battery_percent=80,
            )
        )
        self.assertEqual(decision.status, RiskStatus.DANGER)
        self.assertEqual(decision.priority, 1)

    def test_low_battery_is_warning(self) -> None:
        decision = classify_risk(payload(battery_percent=20))
        self.assertEqual(decision.status, RiskStatus.WARNING)

    def test_extreme_tilt_boundary_is_danger(self) -> None:
        decision = classify_risk(payload(tilt_degree=60))
        self.assertEqual(decision.status, RiskStatus.DANGER)
        self.assertEqual(decision.priority, 3)

    def test_warning_can_hold_multiple_reasons(self) -> None:
        decision = classify_risk(
            payload(distance_front_cm=75, battery_percent=20)
        )
        self.assertEqual(decision.status, RiskStatus.WARNING)
        self.assertEqual(len(decision.reasons), 2)

    def test_missing_device_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "device_id"):
            validate_payload(payload(device_id=""))

    def test_invalid_battery_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "battery_percent"):
            validate_payload(payload(battery_percent=120))


if __name__ == "__main__":
    unittest.main()

