from celery import shared_task

from .priorities import build_hazard_alert, collect_warnings
from .services import (
    ByteTrackTracker,
    GroundedSAMSegmenter,
    YoloObjectDetector,
    ZoeDepthEstimator,
)

_detector: YoloObjectDetector | None = None
_depth_estimator: ZoeDepthEstimator | None = None
_segmenter: GroundedSAMSegmenter | None = None
_tracker: ByteTrackTracker | None = None


def _get_detector() -> YoloObjectDetector:
    global _detector
    if _detector is None:
        _detector = YoloObjectDetector()
    return _detector


def _get_depth() -> ZoeDepthEstimator:
    global _depth_estimator
    if _depth_estimator is None:
        _depth_estimator = ZoeDepthEstimator()
    return _depth_estimator


def _get_segmenter() -> GroundedSAMSegmenter:
    global _segmenter
    if _segmenter is None:
        _segmenter = GroundedSAMSegmenter()
    return _segmenter


def _get_tracker() -> ByteTrackTracker:
    global _tracker
    if _tracker is None:
        _tracker = ByteTrackTracker()
    return _tracker


def process_frame_vision_pipeline(frame_data, frame_id=1):
    detections = _get_detector().detect(frame_data)
    tracked_objects = _get_tracker().update_tracks(detections, frame_id)
    depth_info = _get_depth().estimate_depth(frame_data)
    segmentation_info = _get_segmenter().segment(frame_data, text_prompt="paths, obstacles, and context")

    hazard_alert = build_hazard_alert(tracked_objects)
    warnings = collect_warnings(tracked_objects)

    return {
        "frame_id": frame_id,
        "objects": tracked_objects,
        "depth": depth_info,
        "segmentation": segmentation_info,
        "hazard_alert": hazard_alert,
        "warnings": warnings,
        "detector_ready": _get_detector().ready,
    }


@shared_task
def process_frame_vision_pipeline_task(frame_data, frame_id=1):
    return process_frame_vision_pipeline(frame_data, frame_id)
