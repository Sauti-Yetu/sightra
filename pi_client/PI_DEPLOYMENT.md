# Sightra Pi Zero 2 W — Deployment Guide

This document describes how to deploy the **hardware client** in `pi_client/`. The Pi acts as **camera**, **microphone** (optional offline STT), **speaker** (TTS), and **HTTP client**. A **custom I2S HAT** (or USB audio) can be selected via ALSA device names. **Vosk** runs **on-device** speech-to-text; recognized text is sent as `text_prompt` to the existing API. **YOLO / Gemini** remain on the server only.

---

## SECTION 1: OS Setup

### Raspberry Pi OS Lite

1. Download **Raspberry Pi Imager** from [https://www.raspberrypi.com/software/](https://www.raspberrypi.com/software/).
2. Choose **Raspberry Pi OS (Lite)** — 64-bit recommended for Pi Zero 2 W.
3. Select the correct storage device (SD card).
4. Open **gear icon** (OS customization) before flashing:

   - Set hostname, username/password, locale, keyboard.
   - Enable **SSH** (use password authentication or paste a public key).
   - Configure **WiFi** so the Pi boots on your network (see example below).

5. Flash the image and boot the Pi.

### SSH enable (if not done in Imager)

On the boot partition, create an empty file named `ssh` (no extension) to enable SSH on first boot.

### WiFi setup file example

If you configure WiFi manually on the boot partition (`/boot/firmware` on newer images), create `wpa_supplicant.conf`:

```conf
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="YOUR_WIFI_SSID"
    psk="YOUR_WIFI_PASSWORD"
}
```

Replace `country` with your ISO country code. After first boot, remove or secure this file.

---

## SECTION 2: Dependencies

```bash
sudo apt update
sudo apt install -y libcamera-apps espeak alsa-utils python3-pip
pip3 install --user -r requirements.txt
```

`alsa-utils` provides **`arecord`** / **`aplay`** used for the I2S mic and routed speaker playback. **`requirements.txt`** includes **`requests`** and **`vosk`** (offline STT).

If you prefer an isolated environment:

```bash
python3 -m venv ~/pi_client_venv
source ~/pi_client_venv/bin/activate
pip install -r requirements.txt
```

For systemd, use the **same Python** you installed packages into (or `pip3 install --user` for the `pi` user).

---

## SECTION 3: Camera Test

Verify the camera is detected and the stack works:

```bash
libcamera-hello --list-cameras
libcamera-hello -t 0
```

Capture a still image:

```bash
libcamera-still -o /tmp/test.jpg --width 640 --height 480 --nopreview -t 1
ls -la /tmp/test.jpg
```

If these fail, check ribbon cable, `raspi-config` / overlay for the camera, and power supply.

---

## SECTION 4: Audio — I2S HAT, microphone, TTS

### Quick speaker test (default ALSA device)

```bash
espeak "Sightra ready"
```

### List capture and playback devices (I2S HAT)

```bash
arecord -l
aplay -l
```

Note the **card** and **device** numbers (e.g. `card 1: ... device 0`). Use **`plughw:C,D`** form for rate conversion (recommended for Vosk), e.g. `plughw:1,0`.

### Test microphone (WAV file)

```bash
arecord -D plughw:1,0 -f S16_LE -r 16000 -c 1 -d 3 /tmp/mic-test.wav
aplay -D plughw:1,0 /tmp/mic-test.wav
```

Adjust `-D` to match your HAT. The client uses **16 kHz, mono, 16-bit signed LE** for STT.

### I2S overlay / `config.txt`

Follow your HAT vendor’s instructions (device tree overlay, `dtparam=i2s=on`, etc.). After boot, **card 0** is often HDMI; **I2S** is often **card 1** — verify with `arecord -l`.

### Optional: default device in `~/.asoundrc`

If you set the I2S card as **default** for `pcm.!default`, you can leave `SIGHTRA_CAPTURE_DEVICE` and `SIGHTRA_PLAYBACK_DEVICE` empty and rely on the OS default.

### Offline STT (Vosk)

1. Download a **small** English model (fits Pi Zero 2 W RAM better than large models):

```bash
cd ~
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.tar.gz
tar xf vosk-model-small-en-us-0.15.tar.gz
```

2. Point the client at the extracted directory:

```bash
export SIGHTRA_VOSK_MODEL="$HOME/vosk-model-small-en-us-0.15"
```

Other languages: see [models](https://alphacephei.com/vosk/models).

If `SIGHTRA_VOSK_MODEL` is unset or `SIGHTRA_STT_ENABLED=0`, the client uses **`SIGHTRA_TEXT_PROMPT`** only (no mic recording).

### TTS routing (espeak → I2S speaker)

The client runs **`espeak -w`** to a WAV file, then **`aplay -D`** so playback goes to the **I2S speaker** when `SIGHTRA_PLAYBACK_DEVICE` is set. If unset, `aplay` uses the default device.

---


## SECTION 5: Network Setup

### Backend URL configuration

The client reads **`SIGHTRA_API_URL`** (full URL to the endpoint):

| Deployment | Example |
|------------|---------|
| Django on LAN | `http://192.168.1.50:8000/api/navigation/stream/` |
| VPS (same LAN) | `http://192.168.1.10:8000/api/navigation/stream/` |
| Public HTTPS | `https://sightra.example.com/api/navigation/stream/` |

### Local LAN

- Point `SIGHTRA_API_URL` at the **host:port** where Django runs (e.g. `runserver` or gunicorn behind nginx).
- Ensure the Pi can reach that IP and port (firewall, `ALLOWED_HOSTS` on Django, etc.).

### VPS / domain

- Use your **public hostname** and HTTPS if you terminate TLS with nginx or Caddy.
- The client uses **Python `requests`**; keep the **HTTPS** URL in `SIGHTRA_API_URL` for production.

### HTTPS requirement

- **Recommended** for any traffic over the public internet.
- On a trusted private LAN, HTTP may be acceptable for testing; production deployments should use TLS.

---

## SECTION 6: Install Client

Clone the repository (or copy only the `pi_client` folder) onto the Pi:

```bash
cd ~
git clone <YOUR_REPO_URL> sightra
cd sightra/pi_client
```

For the systemd unit in this repo, the service expects **`/home/pi/pi_client`**. Either:

**Option A — Copy:**

```bash
cp -r ~/sightra/pi_client ~/pi_client
```

**Option B — Adjust systemd:** Edit `ExecStart` and `WorkingDirectory` in `sightra.service` to match `~/sightra/pi_client`.

### Configuration: `.env` (recommended for URLs)

The client loads **`pi_client/.env`** automatically via **`python-dotenv`** (same folder as `main.py`). Copy the template and edit:

```bash
cd /home/pi/pi_client
cp .env.example .env
nano .env
```

**URLs:**

| Variable | Purpose |
|----------|---------|
| **`SIGHTRA_API_URL`** | Full URL to `POST` endpoint, e.g. `https://example.com/api/navigation/stream/` |
| **`SIGHTRA_BASE_URL`** | Optional. If set and `SIGHTRA_API_URL` is empty, the client uses `{SIGHTRA_BASE_URL}/api/navigation/stream/` |

Environment variables set in the shell or systemd **override** values from `.env`.

### Optional: `sightra.env` for systemd only

You can still use **`EnvironmentFile=/home/pi/pi_client/sightra.env`** in systemd (see `sightra.service`). Variables there are visible to the process **before** Python runs; `load_dotenv` also reads `.env`. Prefer **one** of: only `.env`, or only `sightra.env`, or document precedence (shell/systemd wins over `.env` for duplicate keys in typical setups — actually dotenv does not override existing os.environ by default in python-dotenv). **python-dotenv** default: `load_dotenv` does **not** override already-set environment variables. So: `export SIGHTRA_API_URL=...` or systemd `Environment=` overrides `.env`.

Example `.env` (also see `.env.example`):

```bash
SIGHTRA_API_URL=https://your-server.example.com/api/navigation/stream/
SIGHTRA_DEVICE_ID=pi-zero-2w-01
# I2S / ALSA (examples — use values from arecord -l / aplay -l)
SIGHTRA_CAPTURE_DEVICE=plughw:1,0
SIGHTRA_PLAYBACK_DEVICE=plughw:1,0
# Offline STT
SIGHTRA_VOSK_MODEL=/home/pi/vosk-model-small-en-us-0.15
```

Optional variables (see `main.py`):

- `SIGHTRA_TEXT_PROMPT` — used when STT is off, empty, or fails (default: `Describe obstacles ahead`)
- `SIGHTRA_STT_ENABLED` — `1` (default) or `0` to skip mic + Vosk
- `SIGHTRA_RECORD_SECONDS` — mic capture length before each cycle (default `2.5`)
- `SIGHTRA_ESPEAK_VOICE` — e.g. `en`, `en-gb` (optional)
- `SIGHTRA_ESPEAK_SPEED` — words per minute for espeak (default `150`)
- `SIGHTRA_LOOP_SLEEP` — seconds between cycles (default `2.5`)
- `SIGHTRA_REQUEST_TIMEOUT` — HTTP timeout in seconds (default `120`)
- `SIGHTRA_MAX_RETRIES` — number of POST retries on network errors (default `5`)
- `SIGHTRA_RETRY_BACKOFF` — seconds between retries (default `3.0`)

---

## SECTION 7: Run Manual

```bash
cd /home/pi/pi_client
# Configure URL in .env (see above), or:
# export SIGHTRA_API_URL="https://your-server.example.com/api/navigation/stream/"
python3 main.py
```

You should see logs such as:

- recording mic / stt transcript (if Vosk is configured)
- frame captured
- request sent
- response received
- tts speaking / playback to ALSA device

Stop with **Ctrl+C**.

---

## SECTION 8: Enable Auto Start

Install the unit file:

```bash
sudo cp /home/pi/pi_client/sightra.service /etc/systemd/system/sightra.service
sudo systemctl daemon-reload
sudo systemctl enable sightra.service
sudo systemctl start sightra.service
```

Check status:

```bash
sudo systemctl status sightra.service
journalctl -u sightra.service -f
```

---

## SECTION 9: Troubleshooting

### Camera fails

- Run `libcamera-hello --list-cameras`.
- Reseat the camera ribbon cable; ensure the correct port (camera, not display).
- Increase power supply if brownouts occur.
- Confirm `libcamera-still` works manually with the same flags as in `main.py`.

### No response from server

- `curl` the API from the Pi: `curl -v -X POST ...` (with a small JSON body) to verify routing and TLS.
- **HTTPS**: verify certificate validity (self-signed certs need a CA bundle or trust configuration).
- Check Django **ALLOWED_HOSTS**, firewall, and that the server listens on `0.0.0.0` or the Pi’s reachable interface.

### Slow inference

- Slowness is almost always **server-side** (YOLO + Gemini). The Pi only uploads a JPEG.
- Reduce server load by increasing `SIGHTRA_LOOP_SLEEP` (e.g. 5–10 seconds) if needed.

### No audio output (TTS)

- Run `espeak "test"` and `aplay -D plughw:X,Y /usr/share/sounds/alsa/Front_Center.wav` (path may vary) with your device.
- Set **`SIGHTRA_PLAYBACK_DEVICE`** explicitly; verify with `aplay -l`.
- Check `amixer` / `raspi-config` and I2S overlay.

### Microphone / STT fails

- **arecord**: test with Section 4 commands; fix **`SIGHTRA_CAPTURE_DEVICE`**.
- **Vosk**: confirm `SIGHTRA_VOSK_MODEL` points to an **extracted** model directory (contains `am`, `conf`, etc.).
- **Empty transcripts**: reduce background noise, speak during the recording window, or increase `SIGHTRA_RECORD_SECONDS` slightly.
- **Memory**: use **`vosk-model-small`** (or `tiny`) on Pi Zero 2 W; avoid large models.

---

## SECTION 10: Performance Notes

- **Resolution:** `640×480` matches the client and is appropriate for Pi Zero 2 W upload bandwidth and server-side decoding.
- **Interval:** A **2–3 second** loop (default **2.5 s**) avoids overlapping requests while the server processes the previous frame.
- **Pi Zero 2 W limits:** Single-core performance and RAM are modest; **Vosk small** is a reasonable offline STT; avoid **torch** / heavy ML on the Pi.
- **STT per cycle:** Each loop records **~2.5 s** of audio (configurable) before the camera frame — total cycle time includes mic + network + server inference.
- **Network:** WiFi latency and jitter affect perceived responsiveness; use 5 GHz WiFi or Ethernet (USB adapter) if possible.

---

## Design rule (summary)

| Pi | Server |
|----|--------|
| `libcamera-still` capture | YOLO + vision pipeline |
| `arecord` + **Vosk** → `text_prompt` | Gemini (unchanged) |
| Base64 `frame_data` + `text_prompt` POST | Same `/api/navigation/stream/` API |
| **espeak** + **aplay** → I2S speaker | Optional `audio_url` / server TTS (unchanged) |

Use **small Vosk models** only; **no** torch / ultralytics / OpenCV on the Pi for vision.
