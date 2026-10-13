"""
Safety tiers and spatial enrichment for assistive vision output.

Lower tier number = higher urgency for blind / VI users.
"""

from __future__ import annotations

from typing import Any

TIER_EMERGENCY = 0
TIER_CRITICAL = 1
TIER_HIGH = 2
TIER_MEDIUM = 3
TIER_LOW = 4

# COCO-style labels (YOLO) mapped to assistive priority
LABEL_TIER: dict[str, int] = {
    "person": TIER_HIGH,
    "bicycle": TIER_CRITICAL,
    "car": TIER_EMERGENCY,
    "motorcycle": TIER_EMERGENCY,
    "bus": TIER_EMERGENCY,
    "train": TIER_EMERGENCY,
    "truck": TIER_EMERGENCY,
    "fire hydrant": TIER_HIGH,
    "stop sign": TIER_HIGH,
    "parking meter": TIER_MEDIUM,
    "bench": TIER_MEDIUM,
    "bird": TIER_LOW,
    "cat": TIER_MEDIUM,
    "dog": TIER_HIGH,
    "horse": TIER_HIGH,
    "sheep": TIER_LOW,
    "cow": TIER_LOW,
    "elephant": TIER_LOW,
    "bear": TIER_EMERGENCY,
    "zebra": TIER_LOW,
    "giraffe": TIER_LOW,
    "backpack": TIER_MEDIUM,
    "umbrella": TIER_LOW,
    "handbag": TIER_MEDIUM,
    "tie": TIER_LOW,
    "suitcase": TIER_MEDIUM,
    "frisbee": TIER_LOW,
    "skis": TIER_MEDIUM,
    "snowboard": TIER_MEDIUM,
    "sports ball": TIER_LOW,
    "kite": TIER_LOW,
    "baseball bat": TIER_HIGH,
    "skateboard": TIER_HIGH,
    "surfboard": TIER_MEDIUM,
    "tennis racket": TIER_LOW,
    "bottle": TIER_LOW,
    "wine glass": TIER_LOW,
    "cup": TIER_LOW,
    "fork": TIER_LOW,
    "knife": TIER_HIGH,
    "spoon": TIER_LOW,
    "bowl": TIER_LOW,
    "banana": TIER_LOW,
    "chair": TIER_HIGH,
    "couch": TIER_MEDIUM,
    "potted plant": TIER_MEDIUM,
    "bed": TIER_MEDIUM,
    "dining table": TIER_HIGH,
    "toilet": TIER_MEDIUM,
    "tv": TIER_LOW,
    "laptop": TIER_LOW,
    "mouse": TIER_LOW,
    "remote": TIER_LOW,
    "keyboard": TIER_LOW,
    "cell phone": TIER_LOW,
    "microwave": TIER_MEDIUM,
    "oven": TIER_HIGH,
    "toaster": TIER_LOW,
    "sink": TIER_MEDIUM,
    "refrigerator": TIER_MEDIUM,
    "book": TIER_LOW,
    "clock": TIER_LOW,
    "vase": TIER_MEDIUM,
    "scissors": TIER_HIGH,
    "teddy bear": TIER_LOW,
    "hair drier": TIER_LOW,
    "toothbrush": TIER_LOW,
}

# Minimum confidence per tier (reduce false positives on low-risk classes)
TIER_MIN_CONF: dict[int, float] = {
    TIER_EMERGENCY: 0.28,
    TIER_CRITICAL: 0.32,
    TIER_HIGH: 0.38,
    TIER_MEDIUM: 0.42,
    TIER_LOW: 0.48,
}

TIER_LABELS = {
    TIER_EMERGENCY: "emergency",
    TIER_CRITICAL: "critical",
    TIER_HIGH: "high",
    TIER_MEDIUM: "medium",
    TIER_LOW: "low",
}


def label_tier(label: str) -> int:
    return LABEL_TIER.get(label.lower().strip(), TIER_MEDIUM)


def _horizontal_zone(cx: float, frame_w: float) -> str:
    if frame_w <= 0:
        return "center"
    r = cx / frame_w
    if r < 0.33:
        return "left"
    if r > 0.66:
        return "right"
    return "center"


def _distance_band(box_area: float, frame_area: float) -> str:
    if frame_area <= 0:
        return "unknown"
    ratio = box_area / frame_area
    if ratio >= 0.22:
        return "immediate"
    if ratio >= 0.08:
        return "near"
    if ratio >= 0.02:
        return "mid"
    return "far"


def enrich_detection(det: dict[str, Any], frame_w: int, frame_h: int) -> dict[str, Any]:
    x, y, w, h = det.get("box") or [0, 0, 0, 0]
    label = (det.get("label") or "object").lower()
    conf = float(det.get("confidence") or 0)
    tier = label_tier(label)
    cx = x + w / 2
    cy = y + h / 2
    frame_area = max(frame_w * frame_h, 1)
    box_area = max(w * h, 0)
    distance_band = _distance_band(box_area, frame_area)

    # Large person / vehicle in center path → escalate
    if label == "person" and distance_band in ("immediate", "near") and _horizontal_zone(cx, frame_w) == "center":
        tier = min(tier, TIER_CRITICAL)
    if label in ("car", "bus", "truck", "motorcycle", "train", "bicycle") and distance_band in (
        "immediate",
        "near",
    ):
        tier = TIER_EMERGENCY

    priority_score = (5 - tier) * 100 + conf * 50
    if distance_band == "immediate":
        priority_score += 80
    elif distance_band == "near":
        priority_score += 40

    out = dict(det)
    out.update(
        {
            "tier": tier,
            "tier_name": TIER_LABELS.get(tier, "medium"),
            "position": _horizontal_zone(cx, frame_w),
            "vertical": "lower" if cy > frame_h * 0.55 else "upper",
            "distance_band": distance_band,
            "priority_score": round(priority_score, 2),
            "is_hazard": tier <= TIER_HIGH,
            "blocks_path": tier <= TIER_HIGH
            and distance_band in ("immediate", "near")
            and _horizontal_zone(cx, frame_w) in ("center", "left", "right"),
        }
    )
    return out


def filter_by_tier_confidence(detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kept = []
    for d in detections:
        tier = d.get("tier", label_tier(d.get("label", "")))
        min_conf = TIER_MIN_CONF.get(tier, 0.4)
        if float(d.get("confidence") or 0) >= min_conf:
            kept.append(d)
    return kept


def prioritize_objects(detections: list[dict[str, Any]], max_objects: int = 12) -> list[dict[str, Any]]:
    sorted_d = sorted(detections, key=lambda o: (-o.get("priority_score", 0), -float(o.get("confidence") or 0)))
    return sorted_d[:max_objects]


def build_hazard_alert(objects: list[dict[str, Any]]) -> str | None:
    """Short, audio-first alert for the highest-priority hazard."""
    if not objects:
        return None
    top = objects[0]
    if top.get("tier", TIER_LOW) > TIER_HIGH:
        return None
    label = (top.get("label") or "obstacle").replace("_", " ")
    pos = top.get("position") or "ahead"
    dist = top.get("distance_band") or "near"
    tier = top.get("tier", TIER_HIGH)

    if tier == TIER_EMERGENCY:
        prefix = "Urgent."
        if label in ("car", "truck", "bus", "motorcycle", "train", "bicycle"):
            return f"{prefix} Vehicle {dist} on your {pos}. Stop or step back now."
        return f"{prefix} {label.title()} very close {pos}. Stop and reassess."

    if top.get("blocks_path"):
        return f"Caution. {label.title()} {dist}, {pos}. Slow down and consider moving slightly to the side."

    return f"Heads up. {label.title()} {dist} on your {pos}."


def collect_warnings(objects: list[dict[str, Any]]) -> list[str]:
    warnings = []
    for obj in objects:
        if obj.get("tier", TIER_LOW) > TIER_HIGH:
            continue
        label = (obj.get("label") or "object").title()
        warnings.append(
            f"{label} ({obj.get('distance_band', 'near')}, {obj.get('position', 'center')})"
        )
    return warnings[:5]
