# Sightra Pi Zero 2 W — Deployment Guide

This document describes how to deploy the **hardware client** in `pi_client/`. The Raspberry Pi is only a **camera sensor**, **HTTP client**, and **audio output** (`espeak`). All intelligence (YOLO, Gemini, TTS file generation on the server) stays on the Django backend.

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
sudo apt install -y libcamera-apps espeak python3-pip
pip3 install --user requests
```

If you prefer an isolated environment:

```bash
python3 -m venv ~/pi_client_venv
source ~/pi_client_venv/bin/activate
pip install -r requirements.txt
```

The `requirements.txt` in this folder lists only `requests`. For systemd, use the **same Python** you installed packages into (or `pip3 install --user` for the `pi` user).

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

## SECTION 4: Audio Test

```bash
espeak "Sightra ready"
```

If there is no sound, select the correct audio device (USB audio, HDMI, or analog) in your OS settings and test volume.

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

### Environment file (recommended)

Create `/home/pi/pi_client/sightra.env`:

```bash
SIGHTRA_API_URL=https://your-server.example.com/api/navigation/stream/
SIGHTRA_DEVICE_ID=pi-zero-2w-01
```

Optional variables (see `main.py`):

- `SIGHTRA_TEXT_PROMPT` — default: `Describe obstacles ahead`
- `SIGHTRA_LOOP_SLEEP` — seconds between cycles (default `2.5`)
- `SIGHTRA_REQUEST_TIMEOUT` — HTTP timeout in seconds (default `120`)
- `SIGHTRA_MAX_RETRIES` — number of POST retries on network errors (default `5`)
- `SIGHTRA_RETRY_BACKOFF` — seconds between retries (default `3.0`)

---

## SECTION 7: Run Manual

```bash
cd /home/pi/pi_client
export SIGHTRA_API_URL="https://your-server.example.com/api/navigation/stream/"
python3 main.py
```

You should see logs such as:

- frame captured
- request sent
- response received
- speaking text

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

### No audio output

- Run `espeak "test"` manually.
- Check `amixer` / `raspi-config` audio output and volume.
- If using USB speakers, confirm the default ALSA device.

---

## SECTION 10: Performance Notes

- **Resolution:** `640×480` matches the client and is appropriate for Pi Zero 2 W upload bandwidth and server-side decoding.
- **Interval:** A **2–3 second** loop (default **2.5 s**) avoids overlapping requests while the server processes the previous frame.
- **Pi Zero 2 W limits:** Single-core performance and RAM are modest; this client avoids ML libraries (no torch, no ultralytics, no OpenCV on the Pi) for that reason.
- **Network:** WiFi latency and jitter affect perceived responsiveness; use 5 GHz WiFi or Ethernet (USB adapter) if possible.

---

## Design rule (summary)

| Pi | Server |
|----|--------|
| `libcamera-still` capture | YOLO + vision pipeline |
| Base64 POST | Gemini |
| `espeak` playback | Optional `audio_url` / TTS (unchanged) |

Do **not** install heavy ML stacks on the Pi; keep the Pi as a thin client.
