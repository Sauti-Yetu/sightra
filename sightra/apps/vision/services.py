import base64
import logging
import os
from pathlib import Path

import cv2
import numpy as np

from .priorities import (
    enrich_detection,
    filter_by_tier_confidence,
    prioritize_objects,
)

logger = logging.getLogger(__name__)

# Tunable via environment (place custom weights e.g. yolo11s.pt in sightra/ or project root)
YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "models/weights/yolo26n.pt")
YOLO_IMGSZ = int(os.getenv("YOLO_IMGSZ", "384"))
YOLO_MAX_DET = int(os.getenv("YOLO_MAX_DET", "24"))
YOLO_IOU = float(os.getenv("YOLO_IOU", "0.5"))
YOLO_BASE_CONF = float(os.getenv("YOLO_CONF", "0.35"))


def _resolve_model_path() -> str:
    """Find weights file without requiring a fixed cwd."""
    base = Path(__file__).resolve().parents[2]
    name = Path(YOLO_MODEL_PATH)
    candidates = [
        name,
        base / name,
        base / "models" / "weights" / name.name,
        Path.cwd() / name,
        Path.cwd() / "models" / "weights" / name.name,
    ]
    for p in candidates:
        if p.is_file():
            return str(p)
    return str(name)


class YoloObjectDetector:
    def __init__(self):
        self.model = None
        self.ready = False
        self.names: dict[int, str] = {}
        try:
            from ultralytics import YOLO

            path = _resolve_model_path()
            self.model = YOLO(path)
            self.names = getattr(self.model, "names", {}) or {}
            self.ready = True
            logger.info("YoloObjectDetector ready (%s, imgsz=%s).", path, YOLO_IMGSZ)
        except Exception as e:
            logger.error("Failed to load YOLO: %s", e)

    def _decode_image(self, image_b64: str) -> np.ndarray | None:
        if "," in image_b64:
            image_b64 = image_b64.split(",", 1)[1]
        img_bytes = base64.b64decode(image_b64)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    def detect(self, image_b64):
        if not self.ready or not image_b64:
            return []

        try:
            img = self._decode_image(image_b64)
            if img is None:
                return []

            h, w = img.shape[:2]
            # Letterbox-style resize: cap longest side to YOLO_IMGSZ for speed + stability
            scale = min(YOLO_IMGSZ / max(w, h), 1.0)
            if scale < 1.0:
                infer_img = cv2.resize(
                    img,
                    (int(w * scale), int(h * scale)),
                    interpolation=cv2.INTER_AREA,
                )
            else:
                infer_img = img
                scale = 1.0

            results = self.model.predict(
                infer_img,
                imgsz=YOLO_IMGSZ,
                conf=YOLO_BASE_CONF,
                iou=YOLO_IOU,
                max_det=YOLO_MAX_DET,
                verbose=False,
            )

            detections: list[dict] = []
            for r in results:
                if r.boxes is None:
                    continue
                for box in r.boxes:
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    label = self.names.get(cls_id, str(cls_id))
                    x1, y1, x2, y2 = [float(c) / scale for c in box.xyxy[0]]
                    detections.append(
                        {
                            "label": label,
                            "box": [int(x1), int(y1), int(max(x2 - x1, 1)), int(max(y2 - y1, 1))],
                            "confidence": round(conf, 3),
                        }
                    )

            enriched = [enrich_detection(d, w, h) for d in detections]
            enriched = filter_by_tier_confidence(enriched)
            return prioritize_objects(enriched)
        except Exception as e:
            logger.error("YOLO detection error: %s", e)
            return []


class ZoeDepthEstimator:
    def __init__(self):
        self.ready = True

    def estimate_depth(self, image_b64):
        return {"overall_average_distance_m": None}


class GroundedSAMSegmenter:
    def __init__(self):
        self.ready = True

    def segment(self, image_b64, text_prompt="all obstacles"):
        return {}


class ByteTrackTracker:
    def __init__(self):
        self.ready = True
        self._tracks: dict[int, int] = {}

    def update_tracks(self, detections, frame_id):
        tracked = []
        for i, d in enumerate(detections):
            key = hash((d.get("label"), d.get("box", [0, 0, 0, 0])[0] // 40))
            tid = self._tracks.get(key, 1000 + len(self._tracks))
            self._tracks[key] = tid
            item = dict(d)
            item["track_id"] = tid
            tracked.append(item)
        return tracked


def analyze_scene(frame_data, text_prompt, device_id=None, language="en"):
    """Legacy mock endpoint for integration tests without camera pipeline."""
    return {
        "analysis_text": "Obstacle detected ahead. Move slightly to the left.",
        "navigation_hint": "Turn left slightly and continue forward.",
        "objects": [],
        "warnings": ["Obstacle ahead"],
        "metadata": {"source": "sightra_scene_analysis", "processing_mode": "camera_frame"},
    }
