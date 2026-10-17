#!/usr/bin/env python3
"""Generate transparent logo PNG and PWA icons from static/img/sightra-logo.jpg."""

from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise SystemExit("Install Pillow: pip install Pillow")

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "static" / "img" / "sightra-logo.jpg"
OUT_PNG = ROOT / "static" / "img" / "sightra-logo.png"
ICONS = ROOT / "static" / "icons"


def remove_white_bg(img: Image.Image, threshold: int = 235) -> Image.Image:
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if r >= threshold and g >= threshold and b >= threshold:
                pixels[x, y] = (r, g, b, 0)
    return img


def icon_from_logo(logo: Image.Image, size: int) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    scale = min(size / logo.width, size / logo.height) * 0.88
    nw, nh = int(logo.width * scale), int(logo.height * scale)
    resized = logo.resize((nw, nh), Image.Resampling.LANCZOS)
    ox, oy = (size - nw) // 2, (size - nh) // 2
    canvas.paste(resized, (ox, oy), resized)
    return canvas


def main() -> None:
    if not SRC.is_file():
        raise SystemExit(f"Missing source image: {SRC}")
    logo = remove_white_bg(Image.open(SRC))
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    logo.save(OUT_PNG, optimize=True)
    ICONS.mkdir(parents=True, exist_ok=True)
    for size in (72, 96, 128, 144, 152, 192, 384, 512):
        icon = icon_from_logo(logo, size)
        icon.save(ICONS / f"icon-{size}.png", optimize=True)
    print(f"Wrote {OUT_PNG} and icons in {ICONS}")


if __name__ == "__main__":
    main()
