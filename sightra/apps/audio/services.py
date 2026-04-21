import io
import logging
import os
import shutil
import subprocess
import wave

logger = logging.getLogger(__name__)

# espeak-ng --stdout: signed 16-bit mono PCM at this rate (documented default)
_ESPEAK_SAMPLE_RATE = 22050


def _espeak_binary() -> str | None:
    for name in ("espeak-ng", "espeak"):
        path = shutil.which(name)
        if path:
            return path
    return None


class AudioService:
    """TTS via espeak stdout; can write WAV bytes to MEDIA_ROOT for Nginx."""

    def text_to_speech_wav_bytes(self, text: str, speed: int = 150) -> bytes:
        """
        Synthesize speech to a WAV file in memory using espeak-ng/espeak stdout.
        """
        safe = (text or "").replace("\x00", "")[:8000]
        if not safe.strip():
            return _silent_wav_bytes(200)

        exe = _espeak_binary()
        if not exe:
            logger.warning("No espeak-ng or espeak in PATH; returning silent WAV")
            return _silent_wav_bytes(300)

        try:
            pcm = subprocess.check_output(
                [exe, "--stdout", "-s", str(speed), safe],
                stderr=subprocess.PIPE,
                timeout=120,
            )
        except subprocess.CalledProcessError as e:
            logger.error("espeak failed: %s", e.stderr or e)
            return _silent_wav_bytes(300)
        except FileNotFoundError:
            return _silent_wav_bytes(300)

        if not pcm:
            return _silent_wav_bytes(200)

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(_ESPEAK_SAMPLE_RATE)
            wf.writeframes(pcm)
        return buf.getvalue()

    def write_wav_file(self, text: str, path: str, speed: int = 150) -> None:
        """Write synthesized WAV to path (under MEDIA_ROOT)."""
        data = self.text_to_speech_wav_bytes(text, speed=speed)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)

    def transcribe_audio(self, audio_data):
        """
        Stub for processing voice command through Whisper or DeepFilterNet.
        `audio_data` is base64 encoded audio.
        """
        logger.info("Running speech-to-text transcription...")
        return "Can you tell me if the path ahead is clear?"


def _silent_wav_bytes(duration_ms: int) -> bytes:
    n = int(_ESPEAK_SAMPLE_RATE * duration_ms / 1000)
    pcm = b"\x00\x00" * max(1, n)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(_ESPEAK_SAMPLE_RATE)
        wf.writeframes(pcm)
    return buf.getvalue()


_audio_service = AudioService()
