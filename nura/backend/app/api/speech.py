"""Text-to-speech and speech-to-text via ElevenLabs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.api.deps import get_pipeline, require_rate_limit
from app.config import Settings, get_settings
from app.schemas.common import ApiResponse
from app.services.pipeline import VisualPipeline
from app.utils.errors import TTS_UNAVAILABLE, UserFacingError
from app.utils.upload import read_audio_upload

router = APIRouter(tags=["speech"])


class TTSBody(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    speed: float = 1.0


@router.post("/tts")
async def tts(
    body: TTSBody,
    pipeline: VisualPipeline = Depends(get_pipeline),
    _: None = Depends(require_rate_limit),
) -> Response:
    audio = pipeline.speech.synthesize(body.text, speed=body.speed)
    if not audio:
        raise UserFacingError(TTS_UNAVAILABLE, status_code=503)
    return Response(content=audio, media_type="audio/mpeg")


@router.post("/stt", response_model=ApiResponse)
async def stt(
    audio: UploadFile = File(...),
    pipeline: VisualPipeline = Depends(get_pipeline),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_rate_limit),
) -> ApiResponse:
    data, mime = await read_audio_upload(audio, settings.max_audio_bytes)
    text = pipeline.speech.transcribe(data, mime)
    return ApiResponse(
        success=True,
        type="transcript",
        result={"text": text},
        spoken=text,
        confidence=0.9 if text else 0.0,
    )


@router.post("/session/clear", response_model=ApiResponse)
async def clear_session(
    session_id: str = Form(...),
    pipeline: VisualPipeline = Depends(get_pipeline),
) -> ApiResponse:
    pipeline.context.clear(session_id)
    return ApiResponse(success=True, type="session", result={"cleared": True}, session_id=session_id)
