from celery import shared_task
from .services import (
    YoloObjectDetector,
    ZoeDepthEstimator,
    GroundedSAMSegmenter,
    ByteTrackTracker
)

# Instantiate models globally at module level so they are loaded once per worker process
# In a real scenario, you may lazy load these to save memory if not immediately needed.
detector = YoloObjectDetector()
depth_estimator = ZoeDepthEstimator()
segmenter = GroundedSAMSegmenter()
tracker = ByteTrackTracker()

@shared_task
def process_frame_vision_pipeline(frame_data, frame_id=1):
    """
    Executes the full computer vision pipeline on a given frame.
    `frame_data` could be base64 encoded image or URL to image in blob storage.
    """
    
    # 1. Object Detection (YOLO)
    detections = detector.detect(frame_data)
    
    # 2. Tracking (ByteTrack)
    tracked_objects = tracker.update_tracks(detections, frame_id)
    
    # 3. Depth Estimation (ZoeDepth)
    depth_info = depth_estimator.estimate_depth(frame_data)
    
    # 4. Semantic Parsing (GroundedSAM)
    segmentation_info = segmenter.segment(frame_data, text_prompt="paths, obstacles, and context")
    
    # Aggregate reasoning
    metadata = {
        "frame_id": frame_id,
        "objects": tracked_objects,
        "depth": depth_info,
        "segmentation": segmentation_info
    }
    
    return metadata
