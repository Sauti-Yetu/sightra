#!/usr/bin/env python3
"""
Sightra Pi Zero 2 W lightweight client.
Captures frames with libcamera-still, POSTs to the navigation API, speaks via espeak.
All vision/Gemini logic remains on the server.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import time
import uuid

import requests

# --- Config (override with environment variables) ---
SIGHTRA_API_URL = os.environ.get(
    "SIGHTRA_API_URL",
    "http://127.0.0.1:8000/api/navigation/stream/",
)
SIGHTRA_DEVICE_ID = os.environ.get("SIGHTRA_DEVICE_ID", "pi-zero-2w-01")
TEXT_PROMPT = os.environ.get(
    "SIGHTRA_TEXT_PROMPT",
    "Describe obstacles ahead",
)

FRAME_PATH = os.environ.get("SIGHTRA_FRAME_PATH", "/tmp/sightra_frame.jpg")
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


def jpeg_file_to_data_url(path: str) -> str:
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def post_frame(data_url: str) -> dict:
    payload = {
        "frame_data": data_url,
        "text_prompt": TEXT_PROMPT,
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


def speak_analysis(text: str) -> None:
    # Pass text as argv to avoid shell injection; truncate very long strings for espeak stability
    safe = text.replace("\x00", "")[:8000]
    if not safe.strip():
        return
    log(f"speaking text ({len(safe)} chars)")
    subprocess.run(
        ["espeak", safe],
        check=False,
        timeout=300,
    )


def run_cycle() -> None:
    log("capturing frame")
    capture_frame()
    log(f"frame captured -> {FRAME_PATH}")

    data_url = jpeg_file_to_data_url(FRAME_PATH)
    log(f"encoded frame ({len(data_url)} chars data URL prefix ok)")

    body = post_frame(data_url)
    analysis = body.get("analysis_text")
    if analysis:
        log(f"analysis_text: {analysis[:200]}{'...' if len(analysis) > 200 else ''}")
        speak_analysis(str(analysis))
    else:
        log("no analysis_text in response; skipping speech")


def main() -> None:
    log(
        f"starting Sightra Pi client | API={SIGHTRA_API_URL} | device={SIGHTRA_DEVICE_ID}"
    )
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
