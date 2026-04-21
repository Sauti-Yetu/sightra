import os
import uuid

from celery import shared_task
from django.conf import settings

from .services import AudioService

audio_service = AudioService()


def generate_audio_feedback(text, output_filename=None):
    """
    Writes TTS WAV under MEDIA_ROOT for Nginx to serve at MEDIA_URL.
    Synchronous helper (also safe to call from views without Celery queue).
    """
    media_root = settings.MEDIA_ROOT
    os.makedirs(media_root, exist_ok=True)

    if output_filename is None:
        output_filename = f"response_{uuid.uuid4().hex}.wav"

    rel = output_filename.lstrip("/")
    output_path = os.path.join(media_root, rel)
    audio_service.write_wav_file(text, output_path)

    base = settings.MEDIA_URL.rstrip("/") + "/"
    return {"audio_url": f"{base}{rel}"}


@shared_task
def transcribe_user_command(audio_data):
    """
    Transcribes audio payload from user.
    """
    text = audio_service.transcribe_audio(audio_data)
    return {"transcription": text}
