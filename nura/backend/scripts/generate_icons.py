from PIL import Image, ImageDraw
from pathlib import Path

SIZES = [72, 96, 128, 144, 152, 192, 384, 512]
OUT = Path(__file__).resolve().parents[2] / "frontend" / "public" / "icons"


def draw_icon(size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size), (7, 8, 11, 255))
    draw = ImageDraw.Draw(image)
    margin = size * 0.12
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=size * 0.22,
        fill=(18, 20, 26, 255),
    )
    cx, cy = size / 2, size / 2
    for index, radius in enumerate((0.34, 0.26, 0.18)):
        color = (78, 224, 184, 255) if index == 2 else (78, 224, 184, 90 + index * 50)
        box = [cx - size * radius, cy - size * radius, cx + size * radius, cy + size * radius]
        draw.arc(box, start=200, end=340, fill=color, width=max(2, int(size * 0.045)))
    pupil = size * 0.07
    draw.ellipse([cx - pupil, cy - pupil * 0.2, cx + pupil, cy + pupil * 1.6], fill=(245, 247, 250, 255))
    return image


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for size in SIZES:
        draw_icon(size).save(OUT / f"icon-{size}.png")


if __name__ == "__main__":
    main()
