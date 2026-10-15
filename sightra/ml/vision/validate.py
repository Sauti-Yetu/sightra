#!/usr/bin/env python3
"""Validate YOLO26n on coco128 or custom Sightra weights."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_WEIGHTS = ROOT.parent.parent / "models" / "weights" / "yolo26n.pt"
DEFAULT_DATA = ROOT / "data" / "coco128.local.yaml"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--weights", type=Path, default=DEFAULT_WEIGHTS)
    p.add_argument("--data", type=Path, default=DEFAULT_DATA)
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--device", default="cpu")
    return p.parse_args()


def main() -> int:
    from ultralytics import YOLO

    args = parse_args()
    if not args.weights.is_file():
        print(f"Weights not found: {args.weights}")
        return 1
    if not args.data.is_file():
        print("Run download_datasets.py to create coco128.local.yaml")
        return 1

    model = YOLO(str(args.weights))
    metrics = model.val(data=str(args.data), imgsz=args.imgsz, device=args.device)
    print(metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
