from django.test import SimpleTestCase

from apps.vision.priorities import (
    TIER_EMERGENCY,
    build_hazard_alert,
    enrich_detection,
    prioritize_objects,
)


class VisionPriorityTests(SimpleTestCase):
    def test_vehicle_escalates_to_emergency_when_near(self):
        det = enrich_detection(
            {"label": "car", "box": [100, 200, 400, 300], "confidence": 0.55},
            frame_w=640,
            frame_h=480,
        )
        self.assertEqual(det["tier"], TIER_EMERGENCY)
        self.assertTrue(det["blocks_path"])

    def test_hazard_alert_prioritizes_vehicle(self):
        objs = prioritize_objects(
            [
                enrich_detection(
                    {"label": "cup", "box": [10, 10, 30, 30], "confidence": 0.9},
                    640,
                    480,
                ),
                enrich_detection(
                    {"label": "car", "box": [120, 180, 350, 280], "confidence": 0.6},
                    640,
                    480,
                ),
            ]
        )
        alert = build_hazard_alert(objs)
        self.assertIsNotNone(alert)
        self.assertIn("Vehicle", alert)
