"""Follow-up questions against the current scan context."""

from __future__ import annotations

import base64

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.deps import get_pipeline, require_rate_limit, session_id
from app.config import Settings, get_settings
from app.schemas.common import ApiResponse, AudioPayload, Verbosity
from app.services.pipeline import VisualPipeline
from app.utils.errors import INVALID_AUDIO, UserFacingError
from app.utils.upload import read_audio_upload

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=ApiResponse)
async def ask(
    question: str | None = Form(default=None),
    audio: UploadFile | None = File(default=None),
    verbosity: Verbosity = Form("standard"),
    speak: bool = Form(True),
    speed: float = Form(1.0),
    pipeline: VisualPipeline = Depends(get_pipeline),
    settings: Settings = Depends(get_settings),
    session: str = Depends(session_id),
    _: None = Depends(require_rate_limit),
) -> ApiResponse:
    text = (question or "").strip()
    if not text and audio is not None:
        audio_bytes, mime = await read_audio_upload(audio, settings.max_audio_bytes)
        text = pipeline.speech.transcribe(audio_bytes, mime)
    if not text:
        raise UserFacingError(INVALID_AUDIO, status_code=400)

    answer = pipeline.ask(session, text, verbosity)
    audio_payload = None
    if speak and answer["spoken"]:
        try:
            tts = pipeline.speech.synthesize(answer["spoken"], speed=speed)
            audio_payload = AudioPayload(
                mime_type="audio/mpeg",
                base64=base64.b64encode(tts).decode("ascii"),
            )
        except UserFacingError:
            audio_payload = None

    return ApiResponse(
        success=True,
        type="ask",
        result={
            "question": text,
            "answer": answer["summary"],
            "spoken": answer["spoken"],
            "last_scan": answer["last_scan"],
        },
        audio=audio_payload,
        confidence=answer["confidence"],
        spoken=answer["spoken"],
        session_id=session,
    )
