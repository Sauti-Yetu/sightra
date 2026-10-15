from pathlib import Path

from django.test import SimpleTestCase

from apps.vision.services import _resolve_model_path


class YoloWeightsTests(SimpleTestCase):
    def test_yolo26n_weights_shipped(self):
        path = Path(_resolve_model_path())
        self.assertTrue(path.is_file(), f"Missing weights: {path}")
        self.assertGreater(path.stat().st_size, 5_000_000)
