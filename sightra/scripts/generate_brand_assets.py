#!/usr/bin/env python3
"""Generate transparent navbar logo and square PWA icons from the Sightra brand source."""

from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise SystemExit("Install Pillow: pip install Pillow")

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(__file__).resolve().parent / "assets" / "sightra-logo-source.jpg"
OUT_NAV = ROOT / "static" / "img" / "sightra-logo.png"
ICONS = ROOT / "static" / "icons"
BRAND_VERSION = "4"


def remove_white_bg(img: Image.Image, threshold: int = 232) -> Image.Image:
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if r >= threshold and g >= threshold and b >= threshold:
                pixels[x, y] = (255, 255, 255, 0)
            elif r > 200 and g > 200 and b > 200:
                # JPEG fringe
                pixels[x, y] = (r, g, b, min(a, 120))
    return img


def crop_to_content(img: Image.Image, pad: int = 8) -> Image.Image:
    bbox = img.getbbox()
    if not bbox:
        return img
    x0, y0, x1, y1 = bbox
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(img.width, x1 + pad)
    y1 = min(img.height, y1 + pad)
    return img.crop((x0, y0, x1, y1))


def square_icon(mark: Image.Image, size: int, fill: float = 0.9) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    scale = min(size / mark.width, size / mark.height) * fill
    nw, nh = max(1, int(mark.width * scale)), max(1, int(mark.height * scale))
    resized = mark.resize((nw, nh), Image.Resampling.LANCZOS)
    ox, oy = (size - nw) // 2, (size - nh) // 2
    canvas.paste(resized, (ox, oy), resized)
    return canvas


def main() -> None:
    if not SRC.is_file():
        raise SystemExit(f"Missing source image: {SRC}")
    mark = crop_to_content(remove_white_bg(Image.open(SRC)))
    OUT_NAV.parent.mkdir(parents=True, exist_ok=True)
    mark.save(OUT_NAV, optimize=True)
    ICONS.mkdir(parents=True, exist_ok=True)
    for size in (72, 96, 128, 144, 152, 192, 384, 512):
        img = square_icon(mark, size)
        img.save(ICONS / f"icon-{size}.png", optimize=True)
        if size in (192, 512):
            img.save(ICONS / f"app-icon-{size}.png", optimize=True)
    print(f"Brand assets v{BRAND_VERSION}: {OUT_NAV}, icons in {ICONS}")


if __name__ == "__main__":
    main()
