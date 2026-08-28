"""Image preprocessing before vision / OCR."""

from __future__ import annotations

import io

from PIL import Image, ImageOps, UnidentifiedImageError

from app.utils.errors import INVALID_IMAGE, UserFacingError


def preprocess_image(data: bytes, max_dimension: int = 1600) -> bytes:
    try:
        image = Image.open(io.BytesIO(data))
        image = ImageOps.exif_transpose(image)
    except (UnidentifiedImageError, OSError) as exc:
        raise UserFacingError(INVALID_IMAGE, status_code=400) from exc

    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    elif image.mode == "L":
        image = image.convert("RGB")

    width, height = image.size
    longest = max(width, height)
    if longest > max_dimension:
        scale = max_dimension / longest
        image = image.resize(
            (max(1, int(width * scale)), max(1, int(height * scale))),
            Image.Resampling.LANCZOS,
        )

    output = io.BytesIO()
    image.save(output, format="JPEG", quality=85, optimize=True)
    return output.getvalue()
