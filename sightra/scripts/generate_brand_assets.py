#!/usr/bin/env python3
"""Resize the square Sightra mark for navbar, launch, PWA icons, and iOS splash screens.

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
BRAND_VERSION = "7"
BLACK = (0, 0, 0, 255)

SPLASHES = (
    (750, 1334),
    (828, 1792),
    (1125, 2436),
    (1170, 2532),
    (1179, 2556),
    (1242, 2688),
    (1284, 2778),
    (1290, 2796),
    (2048, 2732),
)


def square(img: Image.Image, size: int) -> Image.Image:
    tile = img.convert("RGBA")
    return tile.resize((size, size), Image.Resampling.LANCZOS)


def splash(mark: Image.Image, width: int, height: int) -> Image.Image:
    canvas = Image.new("RGBA", (width, height), BLACK)
    side = max(1, int(min(width, height) * 0.42))
    logo = square(mark, side)
    ox = (width - side) // 2
    oy = (height - side) // 2
    canvas.paste(logo, (ox, oy), logo)
    return canvas.convert("RGB")


def main() -> None:
    if not SRC.is_file():
        raise SystemExit(f"Missing source image: {SRC}")
    mark = Image.open(SRC).convert("RGBA")
    OUT_NAV.parent.mkdir(parents=True, exist_ok=True)
    square(mark, 512).save(OUT_NAV, optimize=True)
    ICONS.mkdir(parents=True, exist_ok=True)
    for size in (72, 96, 128, 144, 152, 180, 192, 384, 512):
        img = square(mark, size)
        img.save(ICONS / f"icon-{size}.png", optimize=True)
        if size in (180, 192, 512):
            img.save(ICONS / f"app-icon-{size}.png", optimize=True)
    for width, height in SPLASHES:
        splash(mark, width, height).save(ICONS / f"splash-{width}x{height}.png", optimize=True)
    print(f"Brand assets v{BRAND_VERSION}: {OUT_NAV}, icons and splash in {ICONS}")


if __name__ == "__main__":
    main()
