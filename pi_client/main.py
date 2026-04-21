#!/usr/bin/env python3
"""
Sightra Pi Zero 2 W client: camera (libcamera-still), optional mic STT (arecord + Vosk),
HTTP POST to the navigation API, TTS (espeak, optional I2S via aplay).
All vision/Gemini logic stays on the server.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import time
import uuid
import wave
from pathlib import Path
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv

# Load pi_client/.env first; real environment variables still override.
_PI_CLIENT_DIR = Path(__file__).resolve().parent
load_dotenv(_PI_CLIENT_DIR / ".env")


def _resolve_public_base() -> str:
    """Single HTTP origin for API + media (no :8000, no HTTPS by default)."""
    b = (os.environ.get("SIGHTRA_PUBLIC_BASE") or os.environ.get("SIGHTRA_BASE_URL") or "").strip().rstrip("/")
    if b:
        return b
    return "http://72.61.88.50"


def _resolve_api_url() -> str:
    """POST /api/navigation/stream/ on same host as PUBLIC_BASE unless overridden."""
    explicit = (os.environ.get("SIGHTRA_API_URL") or "").strip()
    if explicit:
        return explicit
    base = _resolve_public_base()
    return urljoin(base + "/", "api/navigation/stream/")


# --- Config (.env + environment variables) ---
SIGHTRA_PUBLIC_BASE = _resolve_public_base()
SIGHTRA_API_URL = _resolve_api_url()
SIGHTRA_DEVICE_ID = os.environ.get("SIGHTRA_DEVICE_ID", "pi-zero-2w-01")
TEXT_PROMPT = os.environ.get(
    "SIGHTRA_TEXT_PROMPT",
    "Describe obstacles ahead",
)

FRAME_PATH = os.environ.get("SIGHTRA_FRAME_PATH", "/tmp/sightra_frame.jpg")
MIC_WAV_PATH = os.environ.get("SIGHTRA_MIC_WAV_PATH", "/tmp/sightra_mic.wav")
TTS_WAV_PATH = os.environ.get("SIGHTRA_TTS_WAV_PATH", "/tmp/sightra_tts.wav")

# ALSA: I2S or other hats — e.g. plughw:1,0 (use `arecord -l` / `aplay -l`)
SIGHTRA_CAPTURE_DEVICE = os.environ.get("SIGHTRA_CAPTURE_DEVICE", "")  # arecord -D
SIGHTRA_PLAYBACK_DEVICE = os.environ.get("SIGHTRA_PLAYBACK_DEVICE", "")  # aplay -D

# STT: Vosk offline model directory (e.g. ~/vosk-model-small-en-us-0.15)
SIGHTRA_VOSK_MODEL = os.environ.get("SIGHTRA_VOSK_MODEL", "")
SIGHTRA_STT_ENABLED = os.environ.get("SIGHTRA_STT_ENABLED", "1") == "1"
SIGHTRA_RECORD_SECONDS = float(os.environ.get("SIGHTRA_RECORD_SECONDS", "2.5"))

CAPTURE_CMD = [
    "libcamera-still",
    "-o",
    FRAME_PATH,
    "--width",
    "640",
    "--height",
    "480",
    "--nopreview",
    "-t",
    "1",
]

LOOP_SLEEP_SEC = float(os.environ.get("SIGHTRA_LOOP_SLEEP", "2.5"))
REQUEST_TIMEOUT_SEC = float(os.environ.get("SIGHTRA_REQUEST_TIMEOUT", "120"))
MAX_NETWORK_RETRIES = int(os.environ.get("SIGHTRA_MAX_RETRIES", "5"))
RETRY_BACKOFF_SEC = float(os.environ.get("SIGHTRA_RETRY_BACKOFF", "3.0"))

# espeak: optional voice e.g. en, en-gb (fallback when server sends no playable audio)
SIGHTRA_ESPEAK_VOICE = os.environ.get("SIGHTRA_ESPEAK_VOICE", "")
SIGHTRA_ESPEAK_SPEED = os.environ.get("SIGHTRA_ESPEAK_SPEED", "150")
# Prefer server TTS: 1) audio_url over HTTP  2) optional audio_base64 in JSON
SIGHTRA_USE_SERVER_AUDIO = os.environ.get("SIGHTRA_USE_SERVER_AUDIO", "1") == "1"

_vosk_model = None  # lazy singleton


def log(msg: str) -> None:
    print(f"[sightra-pi] {msg}", flush=True)


def capture_frame() -> None:
    subprocess.run(
        CAPTURE_CMD,
        check=True,
        timeout=60,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )


def record_mic() -> None:
    """16 kHz mono S16_LE WAV for Vosk."""
    cmd = ["arecord"]
    if SIGHTRA_CAPTURE_DEVICE:
        cmd.extend(["-D", SIGHTRA_CAPTURE_DEVICE])
    dur = max(1, int(round(SIGHTRA_RECORD_SECONDS)))
    cmd.extend(
        [
            "-f",
            "S16_LE",
            "-r",
            "16000",
            "-c",
            "1",
            "-d",
            str(dur),
            MIC_WAV_PATH,
        ]
    )
    log(f"recording mic -> {MIC_WAV_PATH} ({SIGHTRA_RECORD_SECONDS}s)")
    subprocess.run(
        cmd,
        check=True,
        timeout=int(SIGHTRA_RECORD_SECONDS) + 15,
        stderr=subprocess.PIPE,
    )
    log("mic capture finished")


def load_vosk_model():
    """Return vosk.Model or None if disabled / missing."""
    global _vosk_model
    if not SIGHTRA_STT_ENABLED or not SIGHTRA_VOSK_MODEL:
        return None
    if not os.path.isdir(SIGHTRA_VOSK_MODEL):
        log(f"Vosk model path missing or not a directory: {SIGHTRA_VOSK_MODEL!r}")
        return None
    if _vosk_model is None:
        try:
            from vosk import Model
        except ImportError:
            log("vosk not installed (pip install vosk); using SIGHTRA_TEXT_PROMPT only")
            return None
        log(f"loading Vosk model from {SIGHTRA_VOSK_MODEL}")
        _vosk_model = Model(SIGHTRA_VOSK_MODEL)
    return _vosk_model


def transcribe_wav(wav_path: str, model) -> str:
    from vosk import KaldiRecognizer

    with wave.open(wav_path, "rb") as wf:
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
            log("mic wav must be mono 16-bit for Vosk")
            return ""
        rate = wf.getframerate()
        rec = KaldiRecognizer(model, rate)
        parts: list[str] = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                j = json.loads(rec.Result())
                if j.get("text"):
                    parts.append(j["text"])
        j = json.loads(rec.FinalResult())
        if j.get("text"):
            parts.append(j["text"])
        return " ".join(parts).strip()


def resolve_text_prompt() -> str:
    """Use STT from I2S mic when Vosk is configured; else static TEXT_PROMPT."""
    if not SIGHTRA_STT_ENABLED:
        log("STT disabled (SIGHTRA_STT_ENABLED=0); using SIGHTRA_TEXT_PROMPT")
        return TEXT_PROMPT

    model = load_vosk_model()
    if model is None:
        log("STT skipped (set SIGHTRA_VOSK_MODEL to a Vosk model dir); using SIGHTRA_TEXT_PROMPT")
        return TEXT_PROMPT

    try:
        record_mic()
    except subprocess.CalledProcessError as e:
        log(f"mic recording failed: {e!r}; using SIGHTRA_TEXT_PROMPT")
        return TEXT_PROMPT
    except FileNotFoundError:
        log("arecord not found; install alsa-utils; using SIGHTRA_TEXT_PROMPT")
        return TEXT_PROMPT

    try:
        text = transcribe_wav(MIC_WAV_PATH, model)
    except Exception as e:
        log(f"STT error: {e!r}; using SIGHTRA_TEXT_PROMPT")
        return TEXT_PROMPT

    log(f"stt transcript: {text!r}")
    if text:
        return text
    log("empty STT result; using SIGHTRA_TEXT_PROMPT")
    return TEXT_PROMPT


def jpeg_file_to_data_url(path: str) -> str:
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def absolute_url(path_or_url: str) -> str:
    """Join relative paths like /media/foo.wav to SIGHTRA_PUBLIC_BASE."""
    p = (path_or_url or "").strip()
    if not p:
        return ""
    if p.startswith("http://") or p.startswith("https://"):
        return p
    return urljoin(SIGHTRA_PUBLIC_BASE.rstrip("/") + "/", p.lstrip("/"))


def fetch_audio_wav(url: str) -> bytes:
    log(f"fetching audio: {url}")
    r = requests.get(url, timeout=REQUEST_TIMEOUT_SEC)
    r.raise_for_status()
    log(f"audio bytes received: {len(r.content)}")
    return r.content


def post_frame(data_url: str, text_prompt: str) -> dict:
    payload = {
        "frame_data": data_url,
        "text_prompt": text_prompt,
        "device_id": SIGHTRA_DEVICE_ID,
        "frame_id": f"pi-{uuid.uuid4().hex[:16]}",
    }
    headers = {"Content-Type": "application/json"}
    last_exc: Exception | None = None
    for attempt in range(1, MAX_NETWORK_RETRIES + 1):
        try:
            log(f"request sent (attempt {attempt}/{MAX_NETWORK_RETRIES})")
            r = requests.post(
                SIGHTRA_API_URL,
                data=json.dumps(payload),
                headers=headers,
                timeout=REQUEST_TIMEOUT_SEC,
            )
            r.raise_for_status()
            log("response received")
            return r.json()
        except requests.RequestException as e:
            last_exc = e
            log(f"network error: {e!r}")
            if attempt < MAX_NETWORK_RETRIES:
                log(f"retry in {RETRY_BACKOFF_SEC}s")
                time.sleep(RETRY_BACKOFF_SEC)
    raise last_exc  # type: ignore[misc]


def play_wav_bytes(wav_bytes: bytes) -> None:
    """Play WAV from memory via aplay (no /media download)."""
    if not wav_bytes:
        return
    cmd = ["aplay", "-q"]
    if SIGHTRA_PLAYBACK_DEVICE:
        cmd.extend(["-D", SIGHTRA_PLAYBACK_DEVICE])
    cmd.append("-")
    log(f"aplay from stdin ({len(wav_bytes)} bytes wav)")
    subprocess.run(cmd, input=wav_bytes, check=False, timeout=300)


def speak_analysis_local(text: str) -> None:
    """Fallback TTS on the Pi using espeak + aplay file in /tmp (local only)."""
    safe = text.replace("\x00", "")[:8000]
    if not safe.strip():
        return

    espeak_cmd = ["espeak", "-s", SIGHTRA_ESPEAK_SPEED, "-w", TTS_WAV_PATH]
    if SIGHTRA_ESPEAK_VOICE:
        espeak_cmd.extend(["-v", SIGHTRA_ESPEAK_VOICE])
    espeak_cmd.append(safe)

    log(f"local espeak tts ({len(safe)} chars)")
    r = subprocess.run(espeak_cmd, check=False, timeout=300)
    if r.returncode != 0:
        subprocess.run(["espeak", safe], check=False, timeout=300)
        return

    if SIGHTRA_PLAYBACK_DEVICE:
        subprocess.run(
            ["aplay", "-q", "-D", SIGHTRA_PLAYBACK_DEVICE, TTS_WAV_PATH],
            check=False,
        )
    else:
        subprocess.run(["aplay", "-q", TTS_WAV_PATH], check=False)


def run_cycle() -> None:
    text_prompt = resolve_text_prompt()

    log("capturing frame")
    capture_frame()
    log(f"frame captured -> {FRAME_PATH}")

    data_url = jpeg_file_to_data_url(FRAME_PATH)
    log(f"encoded frame ({len(data_url)} chars data URL prefix ok)")

    body = post_frame(data_url, text_prompt)
    analysis = body.get("analysis_text")
    if analysis:
        log(f"analysis_text: {analysis[:200]}{'...' if len(analysis) > 200 else ''}")

    played = False
    if SIGHTRA_USE_SERVER_AUDIO and body.get("audio_url"):
        try:
            au = absolute_url(body["audio_url"])
            wav_bytes = fetch_audio_wav(au)
            play_wav_bytes(wav_bytes)
            played = True
            log("played server audio from audio_url")
        except Exception as e:
            log(f"server audio_url fetch/play failed: {e!r}")

    if SIGHTRA_USE_SERVER_AUDIO and not played and body.get("audio_base64"):
        try:
            wav_bytes = base64.b64decode(body["audio_base64"])
            play_wav_bytes(wav_bytes)
            played = True
            log("played server audio_base64")
        except Exception as e:
            log(f"server audio decode/play failed: {e!r}")

    if not played and analysis:
        speak_analysis_local(str(analysis))
    elif not played:
        log("no audio (no server audio_base64 and no analysis_text)")


def main() -> None:
    log(
        f"starting Sightra Pi client | public={SIGHTRA_PUBLIC_BASE} | API={SIGHTRA_API_URL} | device={SIGHTRA_DEVICE_ID}"
    )
    log(
        f"audio: capture_dev={SIGHTRA_CAPTURE_DEVICE or 'default'} "
        f"playback_dev={SIGHTRA_PLAYBACK_DEVICE or 'default'} "
        f"stt={'vosk' if SIGHTRA_VOSK_MODEL else 'off'}"
    )
    log(f"server_audio: {'on' if SIGHTRA_USE_SERVER_AUDIO else 'off'}")
    while True:
        try:
            run_cycle()
        except subprocess.CalledProcessError as e:
            log(f"capture failed: {e!r}")
        except FileNotFoundError as e:
            log(f"file error: {e!r}")
        except requests.RequestException as e:
            log(f"request failed after retries: {e!r}")
        except json.JSONDecodeError as e:
            log(f"invalid JSON response: {e!r}")
        except OSError as e:
            log(f"os error: {e!r}")
        except Exception as e:
            log(f"unexpected error: {e!r}")

        log(f"sleep {LOOP_SLEEP_SEC}s")
        time.sleep(LOOP_SLEEP_SEC)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("stopped by user")
        sys.exit(0)
