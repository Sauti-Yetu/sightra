"""Upload validation for images and audio."""

from __future__ import annotations

import io
from typing import Iterable

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.utils.errors import FILE_TOO_LARGE, INVALID_AUDIO, INVALID_IMAGE, UserFacingError

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_AUDIO_TYPES = {
    "audio/webm",
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp4",
    "audio/m4a",
    "audio/ogg",
    "audio/mp3",
    "application/octet-stream",
}
ALLOWED_AUDIO_EXT = {".webm", ".wav", ".mp3", ".m4a", ".mp4", ".ogg", ".aac"}


def _extension(filename: str | None) -> str:
    if not filename or "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()


async def read_upload(
    upload: UploadFile,
    *,
    max_bytes: int,
    allowed_types: Iterable[str],
    allowed_ext: Iterable[str],
    invalid_message: str,
) -> tuple[bytes, str]:
    content_type = (upload.content_type or "").split(";")[0].strip().lower()
    ext = _extension(upload.filename)
    if content_type not in allowed_types and ext not in allowed_ext:
        raise UserFacingError(invalid_message, status_code=400)

    data = await upload.read()
    if not data:
        raise UserFacingError(invalid_message, status_code=400)
    if len(data) > max_bytes:
        raise UserFacingError(FILE_TOO_LARGE, status_code=413)
    return data, content_type or "application/octet-stream"


async def read_image_upload(upload: UploadFile, max_bytes: int) -> bytes:
    data, _ = await read_upload(
        upload,
        max_bytes=max_bytes,
        allowed_types=ALLOWED_IMAGE_TYPES,
        allowed_ext=ALLOWED_IMAGE_EXT,
        invalid_message=INVALID_IMAGE,
    )
    try:
        image = Image.open(io.BytesIO(data))
        image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise UserFacingError(INVALID_IMAGE, status_code=400) from exc
    return data


async def read_audio_upload(upload: UploadFile, max_bytes: int) -> tuple[bytes, str]:
    data, content_type = await read_upload(
        upload,
        max_bytes=max_bytes,
        allowed_types=ALLOWED_AUDIO_TYPES,
        allowed_ext=ALLOWED_AUDIO_EXT,
        invalid_message=INVALID_AUDIO,
    )
    return data, content_type
