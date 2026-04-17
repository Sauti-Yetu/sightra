import logging
import base64
import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Maximum width to resize frames to before YOLO inference.
# Smaller = faster; 416px gives a good speed/accuracy trade-off for nano models.
YOLO_INFER_WIDTH = 416

class YoloObjectDetector:
    def __init__(self):
        try:
            from ultralytics import YOLO
            self.model = YOLO("yolo11n.pt")
            self.ready = True
            logger.info("YoloObjectDetector ready.")
        except Exception as e:
            logger.error(f"Failed to load YOLO: {e}")
            self.ready = False

    def _resize_for_inference(self, img: np.ndarray) -> tuple[np.ndarray, float]:
        """Downscale img width to YOLO_INFER_WIDTH, return (resized_img, scale_factor)."""
        h, w = img.shape[:2]
        if w <= YOLO_INFER_WIDTH:
            return img, 1.0
        scale = YOLO_INFER_WIDTH / w
        new_w = YOLO_INFER_WIDTH
        new_h = int(h * scale)
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        return resized, scale

    def detect(self, image_b64):
        """
        Runs YOLO object detection on the provided base64 frame.
        """
        if not self.ready or not image_b64:
            return []
            
        try:
            logger.info("Running YOLO object detection...")
            if ',' in image_b64:
                image_b64 = image_b64.split(',')[1]
                
            img_bytes = base64.b64decode(image_b64)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if img is None:
                return []

            # Resize once for faster inference, keep scale to map boxes back
            infer_img, scale = self._resize_for_inference(img)

            results = self.model(
                infer_img,
                verbose=False,
                stream=True,       # generator mode – lower peak memory
                imgsz=YOLO_INFER_WIDTH,
            )

            detections = []
            for r in results:
                for box in r.boxes:
                    conf = float(box.conf[0])
                    if conf >= 0.35:  # slightly relaxed for faster moving objects
                        cls_id = int(box.cls[0])
                        label = self.model.names[cls_id]
                        # Map coordinates back to original image scale
                        x1, y1, x2, y2 = [int(float(c) / scale) for c in box.xyxy[0]]
                        w = x2 - x1
                        h = y2 - y1

                        detections.append({
                            "label": label,
                            "box": [x1, y1, w, h],
                            "confidence": round(conf, 2)
                        })
            return detections
        except Exception as e:
            logger.error(f"YOLO detection error: {e}")
            return []

class ZoeDepthEstimator:
    def __init__(self):
        self.ready = True

    def estimate_depth(self, image_b64):
        # Stub returning no hallucinated data
        return {"overall_average_distance_m": None}

class GroundedSAMSegmenter:
    def __init__(self):
        self.ready = True

    def segment(self, image_b64, text_prompt="all obstacles"):
        # Stub returning no hallucinated data
        return {}

class ByteTrackTracker:
    def __init__(self):
        self.ready = True

    def update_tracks(self, detections, frame_id):
        # Simple placeholder assigning track ID to YOLO detections
        tracked_objects = []
        for i, d in enumerate(detections):
            d["track_id"] = i + 1000
            tracked_objects.append(d)
        return tracked_objects

