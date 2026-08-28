"""Visual reading endpoints."""

from __future__ import annotations

import base64

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.deps import get_pipeline, require_rate_limit, session_id
from app.config import Settings, get_settings
from app.schemas.common import ApiResponse, AudioPayload, ReadMode, Verbosity
from app.services.pipeline import VisualPipeline
from app.utils.errors import UserFacingError
from app.utils.upload import read_image_upload

router = APIRouter(tags=["analysis"])


def _envelope(result, session: str, audio_bytes: bytes | None) -> ApiResponse:
    audio = None
    if audio_bytes:
        audio = AudioPayload(
            mime_type="audio/mpeg",
            base64=base64.b64encode(audio_bytes).decode("ascii"),
        )
    return ApiResponse(
        success=True,
        type=result.type,
        result=result.model_dump(),
        audio=audio,
        confidence=result.confidence,
        spoken=result.spoken,
        session_id=session,
    )


async def _run_mode(
    upload: UploadFile,
    mode: ReadMode,
    verbosity: Verbosity,
    speak: bool,
    speed: float,
    pipeline: VisualPipeline,
    settings: Settings,
    session: str,
) -> ApiResponse:
    image = await read_image_upload(upload, settings.max_image_bytes)
    result = pipeline.analyze(image, mode, verbosity, session)
    audio_bytes = None
    if speak and result.spoken:
        try:
            audio_bytes = pipeline.speech.synthesize(result.spoken, speed=speed)
        except UserFacingError:
            audio_bytes = None
    return _envelope(result, session, audio_bytes)


@router.post("/analyze", response_model=ApiResponse)
async def analyze(
    image: UploadFile = File(...),
    mode: ReadMode = Form("read"),
    verbosity: Verbosity = Form("standard"),
    speak: bool = Form(True),
    speed: float = Form(1.0),
    pipeline: VisualPipeline = Depends(get_pipeline),
    settings: Settings = Depends(get_settings),
    session: str = Depends(session_id),
    _: None = Depends(require_rate_limit),
) -> ApiResponse:
    return await _run_mode(image, mode, verbosity, speak, speed, pipeline, settings, session)


@router.post("/read", response_model=ApiResponse)
async def read(
    image: UploadFile = File(...),
    verbosity: Verbosity = Form("standard"),
    speak: bool = Form(True),
    speed: float = Form(1.0),
    pipeline: VisualPipeline = Depends(get_pipeline),
    settings: Settings = Depends(get_settings),
    session: str = Depends(session_id),
    _: None = Depends(require_rate_limit),
) -> ApiResponse:
    return await _run_mode(image, "read", verbosity, speak, speed, pipeline, settings, session)


@router.post("/currency", response_model=ApiResponse)
async def currency(
    image: UploadFile = File(...),
    verbosity: Verbosity = Form("standard"),
    speak: bool = Form(True),
    speed: float = Form(1.0),
    pipeline: VisualPipeline = Depends(get_pipeline),
    settings: Settings = Depends(get_settings),
    session: str = Depends(session_id),
    _: None = Depends(require_rate_limit),
) -> ApiResponse:
    return await _run_mode(image, "currency", verbosity, speak, speed, pipeline, settings, session)


@router.post("/sign", response_model=ApiResponse)
async def sign(
    image: UploadFile = File(...),
    verbosity: Verbosity = Form("standard"),
    speak: bool = Form(True),
    speed: float = Form(1.0),
    pipeline: VisualPipeline = Depends(get_pipeline),
    settings: Settings = Depends(get_settings),
    session: str = Depends(session_id),
    _: None = Depends(require_rate_limit),
) -> ApiResponse:
    return await _run_mode(image, "sign", verbosity, speak, speed, pipeline, settings, session)


@router.post("/document", response_model=ApiResponse)
async def document(
    image: UploadFile = File(...),
    verbosity: Verbosity = Form("standard"),
    speak: bool = Form(True),
    speed: float = Form(1.0),
    pipeline: VisualPipeline = Depends(get_pipeline),
    settings: Settings = Depends(get_settings),
    session: str = Depends(session_id),
    _: None = Depends(require_rate_limit),
) -> ApiResponse:
    return await _run_mode(image, "document", verbosity, speak, speed, pipeline, settings, session)
