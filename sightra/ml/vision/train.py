#!/usr/bin/env python3
"""
Fine-tune YOLO26n for Sightra (mobility-focused classes).

Examples:
  python train.py --data coco128.local.yaml --epochs 30
  python train.py --data sightra_mobility.yaml --classes 0,1,2,3,5,7,56
"""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_WEIGHTS = ROOT.parent.parent / "models" / "weights" / "yolo26n.pt"
DEFAULT_DATA = ROOT / "data" / "coco128.local.yaml"
MOBILITY_CLASS_IDS = [
    0, 1, 2, 3, 5, 6, 7, 9, 11, 13, 15, 16, 24, 26, 36, 56, 57, 58, 60, 67
]


def parse_args():
    p = argparse.ArgumentParser(description="Train Sightra YOLO26n")
    p.add_argument("--weights", type=Path, default=DEFAULT_WEIGHTS)
    p.add_argument("--data", type=Path, default=DEFAULT_DATA)
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--device", default="cpu")
    p.add_argument("--project", type=Path, default=ROOT / "runs" / "detect")
    p.add_argument("--name", default="sightra-yolo26n")
    p.add_argument(
        "--classes",
        type=str,
        default="",
        help="Optional comma-separated COCO class ids (mobility subset)",
    )
    p.add_argument(
        "--mobility",
        action="store_true",
        help="Train on Sightra mobility class subset (see MOBILITY_CLASS_IDS)",
    )
    return p.parse_args()


def main() -> int:
    from ultralytics import YOLO

    args = parse_args()
    if not args.weights.is_file():
        print(f"Weights not found: {args.weights}")
        return 1
    if not args.data.is_file():
        print(f"Dataset yaml missing: {args.data}. Run download_datasets.py first.")
        return 1

    model = YOLO(str(args.weights))
    train_kwargs = dict(
        data=str(args.data),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=str(args.project),
        name=args.name,
        patience=15,
        save=True,
        plots=True,
        verbose=True,
    )
    if args.mobility:
        train_kwargs["classes"] = MOBILITY_CLASS_IDS
    elif args.classes.strip():
        train_kwargs["classes"] = [int(x) for x in args.classes.split(",") if x.strip()]

    model.train(**train_kwargs)
    best = args.project / args.name / "weights" / "best.pt"
    if best.is_file():
        dest = ROOT.parent.parent / "models" / "weights" / "sightra_yolo26n.pt"
        shutil = __import__("shutil")
        shutil.copy2(best, dest)
        print(f"Exported fine-tuned weights to {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
