#!/usr/bin/env python3
"""Download Ultralytics demo datasets (coco128) for train/val smoke tests."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATASETS = ROOT / "datasets"


def main() -> int:
    try:
        from ultralytics.utils.downloads import download
    except ImportError:
        print("Install ultralytics first: pip install ultralytics", file=sys.stderr)
        return 1

    DATASETS.mkdir(parents=True, exist_ok=True)
    coco128_dir = DATASETS / "coco128"
    if not (coco128_dir / "images").exists():
        print("Downloading coco128 …")
        zip_url = "https://github.com/ultralytics/assets/releases/download/v0.0.0/coco128.zip"
        download(zip_url, dir=DATASETS, unzip=True)
    else:
        print("coco128 already present.")

    # Patch local yaml to point at our datasets folder
    src_yaml = DATA / "coco128.yaml"
    out_yaml = DATA / "coco128.local.yaml"
    text = src_yaml.read_text(encoding="utf-8")
    text = text.replace("path: ../datasets/coco128", f"path: {coco128_dir.resolve()}")
    out_yaml.write_text(text, encoding="utf-8")
    print(f"Wrote {out_yaml}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
