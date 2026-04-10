from celery import shared_task
import os
from .services import AudioService

audio_service = AudioService()

@shared_task
def generate_audio_feedback(text, output_filename="response.wav"):
    """
    Converts Gemini analysis text into speech audio.
    Returns the URL/path to the generated audio file.
    """
    output_path = os.path.join("/tmp", output_filename)
    audio_file_path = audio_service.save_text_to_speech(text, output_path)
    # In a real django app, this would be saved to MEDIA_ROOT 
    # to be served statically, or streamed directly.
    return {"audio_url": f"/media/{output_filename}"}

@shared_task
def transcribe_user_command(audio_data):
    """
    Transcribes audio payload from user.
    """
    text = audio_service.transcribe_audio(audio_data)
    return {"transcription": text}
