import logging
import base64
import cv2
import numpy as np

logger = logging.getLogger(__name__)

class YoloObjectDetector:
    def __init__(self):
        try:
            from ultralytics import YOLO
            self.model = YOLO("yolo11n.pt")
            self.ready = True
        except Exception as e:
            logger.error(f"Failed to load YOLO: {e}")
            self.ready = False

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

            results = self.model(img, verbose=False)
            
            detections = []
            for r in results:
                for box in r.boxes:
                    conf = float(box.conf[0])
                    if conf >= 0.4:  # 40% confidence threshold
                        cls_id = int(box.cls[0])
                        label = self.model.names[cls_id]
                        x1, y1, x2, y2 = [int(float(c)) for c in box.xyxy[0]]
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

