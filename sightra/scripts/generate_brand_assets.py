#!/usr/bin/env python3
"""Resize the square Sightra mark for navbar, launch, and PWA icons.

The brand tile is black. Do not strip the background.
"""

from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise SystemExit("Install Pillow: pip install Pillow")

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(__file__).resolve().parent / "assets" / "sightra-logo-source.png"
OUT_NAV = ROOT / "static" / "img" / "sightra-logo.png"
ICONS = ROOT / "static" / "icons"
BRAND_VERSION = "6"


def square(img: Image.Image, size: int) -> Image.Image:
    tile = img.convert("RGBA")
    return tile.resize((size, size), Image.Resampling.LANCZOS)


def main() -> None:
    if not SRC.is_file():
        raise SystemExit(f"Missing source image: {SRC}")
    mark = Image.open(SRC).convert("RGBA")
    OUT_NAV.parent.mkdir(parents=True, exist_ok=True)
    square(mark, 512).save(OUT_NAV, optimize=True)
    ICONS.mkdir(parents=True, exist_ok=True)
    for size in (72, 96, 128, 144, 152, 192, 384, 512):
        img = square(mark, size)
        img.save(ICONS / f"icon-{size}.png", optimize=True)
        if size in (192, 512):
            img.save(ICONS / f"app-icon-{size}.png", optimize=True)
    print(f"Brand assets v{BRAND_VERSION}: {OUT_NAV}, icons in {ICONS}")


if __name__ == "__main__":
    main()
