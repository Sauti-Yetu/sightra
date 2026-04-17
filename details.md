# Sightra — Current System Documentation

This document describes **only what exists today** in the repository: behavior, structure, and integration points. It does not propose changes or future architecture.

---

## 1. System overview

### What the application does

**Sightra** is a **Django** web application that presents a mobile-style, dark-themed user interface for **environment awareness and navigation assistance** aimed at visually impaired users. The server combines:

- **Computer vision** (partially implemented: real YOLO object detection; other vision steps are stubs).
- **Google Gemini** (via the `google.generativeai` Python SDK) to turn structured vision metadata into a short spoken-style description.
- **Text-to-speech** on the server using **pyttsx3** (when the engine initializes), with files written under `/tmp` and a **logical** URL path returned in JSON.

The **only end-to-end automated flow** wired in the codebase is: **Vision page** → browser **camera** → **HTTP POST** to the Django API → vision pipeline + Gemini + TTS → JSON response; the browser uses the **Web Speech API** (`speechSynthesis`) to read `analysis_text` aloud.

Other pages (**home**, **voice assistant**, **settings**) are **static templates** (layout and demo copy). They do not call the navigation API or Gemini from the frontend in the current code.

### Main purpose

Provide a **web UI** and a **backend endpoint** that accepts a **base64-encoded camera frame**, runs detection/metadata extraction, asks Gemini for a **brief navigation-oriented description**, optionally generates a **WAV** file server-side, and returns **text plus metadata** to the client.

### Key features (as implemented)

| Area | Behavior |
|------|----------|
| **Pages** | `index` (dashboard), `vision` (live camera + scan loop), `voice_assistant` (static assistant UI), `settings` (static controls + client-side-only interactions). |
| **API** | `POST /api/navigation/stream/` accepts `frame_data`, optional `text_prompt`, optional `frame_id`; returns `analysis_text`, `audio_url`, `metadata`. |
| **Vision** | YOLO (`yolo11n.pt`) on decoded JPEG frames; ByteTrack wrapper assigns synthetic track IDs; ZoeDepth and GroundedSAM classes return **stub** data. |
| **Gemini** | Text-only request: system + user prompts including **JSON vision metadata** (not the raw image in the current implementation). |
| **Speech output** | Primary: browser **SpeechSynthesisUtterance** with Gemini text. Secondary: server TTS to `/tmp` + `audio_url` string in JSON (media serving not configured in `settings.py`). |

---

## 2. Project structure

Repository layout (relevant portions):

```
/opt/sightra/
├── details.md                 # This document
└── sightra/                   # Django project root (manage.py lives here)
    ├── manage.py
    ├── requirements.txt
    ├── db.sqlite3             # Default SQLite DB (Django)
    ├── templates/             # Server-rendered HTML
    │   ├── index.html
    │   ├── vision.html
    │   ├── voice_assistant.html
    │   ├── settings.html
    │   └── bottom_nav.html
    ├── sightra/               # Project package
    │   ├── settings.py
    │   ├── urls.py            # Root URLconf
    │   ├── wsgi.py
    │   ├── asgi.py
    │   └── celery.py          # Celery app instance
    └── apps/
        ├── accounts/          # Scaffold: empty urls, no views wired
        ├── audio/             # AudioService, Celery tasks, no HTTP routes in urls.py
        ├── core/              # GeminiAnalyzer, analyze_frame_context task
        ├── navigation/        # NavigationStreamView → stream API
        ├── settings/          # Django app named "settings"; page view only
        └── vision/            # Vision pipeline services and task
```

### Major files and folders

| Path | Role |
|------|------|
| `sightra/sightra/settings.py` | Django settings: `INSTALLED_APPS`, SQLite, templates dir, static URL, Celery broker (`redis://localhost:6379/0`), `GEMINI_API_KEY` read from environment with a placeholder default. |
| `sightra/sightra/urls.py` | Maps `/`, `/vision/`, `/settings/`, `/voice_assistant/` to template views; includes `api/*` URLconfs from apps. |
| `sightra/apps/navigation/views.py` | `NavigationStreamView`: orchestrates `analyze_frame_context` and `generate_audio_feedback`, returns DRF `Response`. |
| `sightra/apps/core/services.py` | `GeminiAnalyzer`: configures Gemini, builds prompts, calls `generate_content`. |
| `sightra/apps/core/tasks.py` | `analyze_frame_context`: runs `process_frame_vision_pipeline` then `analyzer.analyze_scene`. |
| `sightra/apps/vision/services.py` | `YoloObjectDetector`, `ZoeDepthEstimator`, `GroundedSAMSegmenter`, `ByteTrackTracker`. |
| `sightra/apps/vision/tasks.py` | `process_frame_vision_pipeline` Celery task; loads models at import time. |
| `sightra/apps/audio/services.py` | `AudioService`: pyttsx3 TTS and stub `transcribe_audio`. |
| `sightra/apps/audio/tasks.py` | `generate_audio_feedback`, `transcribe_user_command` Celery tasks. |
| `sightra/templates/vision.html` | Camera (`getUserMedia`), canvas capture, `fetch` to navigation API, `speechSynthesis`, dynamic bounding boxes from `metadata.objects`. |

**Empty URL modules:** `apps/core/urls.py`, `apps/vision/urls.py`, `apps/audio/urls.py`, `apps/settings/urls.py`, `apps/accounts/urls.py` define **no paths** (empty `urlpatterns`). Only `apps/navigation/urls.py` registers a route under `api/navigation/`.

---

## 3. Frontend analysis

### How the frontend works

- **Stack:** Server-rendered **HTML** with **Tailwind CSS** loaded from the CDN (`cdn.tailwindcss.com`), **Google Fonts** (Lexend, Inter), **Material Symbols** icons. No separate frontend build (no `package.json`, no React/Vue bundle).
- **Shared chrome:** `bottom_nav.html` is included on several pages; a small script highlights the active tab from `window.location.pathname`.

### Camera access

Implemented only in `templates/vision.html`:

- Uses **`navigator.mediaDevices.getUserMedia`**.
- First tries `{ video: { facingMode: "environment" } }` (rear camera on phones).
- On failure, falls back to `{ video: true }`.
- On total failure, logs to console and **`alert("Please enable camera access...")`**.

The stream is attached to a **`<video>`** element (`#cameraElement`) with `autoplay` and `playsinline`.

### Frame capture

- Hidden **`<canvas>`** (`#canvasElement`).
- On each analysis step, script sets `canvas.width` / `canvas.height` from `video.videoWidth` / `video.videoHeight` (defaults 640×480 if zero).
- **`drawImage(video, 0, 0)`** copies the current frame.
- **`canvas.toDataURL('image/jpeg', 0.5)`** produces a **data URL** (base64 JPEG), used as `frame_data`.

### How data is sent

- **`fetch('/api/navigation/stream/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ frame_data, text_prompt }) })`**.
- Default `text_prompt` in code: `"Describe any obstacles or pathways ahead."`
- Optional `frame_id` can be sent; if omitted, the server uses `int(time.time())`.

### UI flow and interaction

1. **Vision page loads** → `startCamera()` runs immediately.
2. User taps **“INITIATE SIGHT SCAN”** → toggles `isScanning`, starts **`captureAndAnalyze()`** loop.
3. Each iteration: capture frame → POST → **`updateDynamicUI(data.metadata)`** (bounding boxes/alerts from `metadata.objects`) → **`SpeechSynthesisUtterance(data.analysis_text)`** → on end/error, schedules the next capture (via `requestAnimationFrame` or `setTimeout`).
4. User taps again to stop → **`stopCamera()`**, clears dynamic UI, cancels `speechSynthesis`.

**Other pages:**

- **`index.html`:** Marketing/dashboard layout; static image URL; links to `/voice_assistant/` only. No camera, no API calls.
- **`voice_assistant.html`:** Static “listening” and conversation **mock** content; buttons are not wired to APIs.
- **`settings.html`:** Client-side-only controls (sensitivity buttons, language row styling, toggles, sliders). **No persistence** to backend.

---

## 4. Backend / API usage

### Backend

There **is** a **Django + Django REST framework** backend.

### API surface (actual routes)

| Method | Path | Handler |
|--------|------|---------|
| GET | `/` | `apps.core.views.index` → `index.html` |
| GET | `/vision/` | `apps.vision.views.vision` → `vision.html` |
| GET | `/voice_assistant/` | `apps.audio.views.voice_assistant` → `voice_assistant.html` |
| GET | `/settings/` | `apps.settings.views.settings_view` → `settings.html` |
| POST | `/api/navigation/stream/` | `NavigationStreamView` |

Admin: `GET /admin/`. Other `api/*` includes point at **empty** urlconfs except navigation.

### Gemini API usage (where and how keys are handled)

- **`apps/core/services.py`**
  - `load_dotenv()` so a `.env` file (if present) is loaded into the process environment.
  - `genai.configure(api_key=os.getenv("GEMINI_API_KEY"))`.
- **`sightra/settings.py`**
  - Defines `GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-gemini-api-key-here")` (the `GeminiAnalyzer` does **not** import this setting for configuration; it uses `os.getenv` directly in `services.py`).

### Request / response shape (navigation stream)

**Request (JSON body, typical):**

- `frame_data` (required): string, expected to be a base64 image or data URL (YOLO strips a `data:*;base64,` prefix if a comma is present).
- `text_prompt` (optional): string, passed into Gemini as “User Voice Command/Query”.
- `frame_id` (optional): defaults to server-side `int(time.time())` if missing.

**Response (JSON, 200):**

- `message`: `"Analysis completed successfully"`
- `analysis_text`: string from Gemini (or an error string from the analyzer on failure).
- `audio_url`: string like `"/media/response_{frame_id}.wav"` from `generate_audio_feedback` (file path is `/tmp/...` on disk).
- `metadata`: object returned by `process_frame_vision_pipeline` (frame id, objects, depth, segmentation).

**Error response:**

- `400` if `frame_data` is missing: `{"error": "frame_data is required"}`.

### Celery vs synchronous execution

Tasks use **`@shared_task`**, but **`NavigationStreamView` calls `analyze_frame_context(...)` and `generate_audio_feedback(...)` as ordinary Python functions** (no `.delay()` / `.apply_async()` in the view). So the **HTTP request runs the task bodies in the same process/thread as the request**, not via a Celery worker queue, unless Celery’s direct-call behavior is relied on differently. The code comments mention async patterns but the implemented path is **synchronous end-to-end** for that request.

---

## 5. AI / Gemini integration

### Are images sent to Gemini?

**No.** `GeminiAnalyzer.analyze_scene` builds **text-only** content:

- `system_prompt`: instructs the model to act as a navigation assistant using **scene metadata** (objects, depth, segmentation).
- `user_prompt`: includes `json.dumps(vision_metadata, indent=2)` and optionally the user text prompt, plus a line asking for a **brief audio-ready description**.

The code comment in `analyze_scene` states that ideally the raw image could be attached for Gemini Vision; that is **not** implemented—the call is `self.model.generate_content([system_prompt, user_prompt])` with **two strings**.

### Model and SDK

- SDK: **`google.generativeai`** (`import google.generativeai as genai`).
- Model name string: **`gemini-3.1-flash-lite-preview`** (`GenerativeModel`).

### Prompts (summary)

- **System:** Empathetic navigation assistant; input is **metadata from CV models** (detection, depth, segmentation); output should be concise, clear, reassuring; highlight safe paths and obstacles.
- **User:** Labeled JSON for “Vision Metadata from Frame”; optional “User Voice Command/Query”; closing instruction for a **safe, confident, very brief audio-ready** description.

### Response handling

- On success: **`response.text`** is returned to the caller and surfaced as **`analysis_text`** in the API JSON.
- On exception: logs error and returns the fixed string: `"An error occurred while analyzing the scene. Please proceed with caution."`

### Vision pipeline output (what Gemini actually sees)

From `process_frame_vision_pipeline` (`apps/vision/tasks.py`), `metadata` contains:

- `frame_id`
- `objects`: from YOLO + `ByteTrackTracker.update_tracks` (track id = index + 1000)
- `depth`: from `ZoeDepthEstimator` — currently **`{"overall_average_distance_m": None}`**
- `segmentation`: from `GroundedSAMSegmenter` — currently **`{}`**

So Gemini primarily reasons over **YOLO labels, boxes, and confidence**, plus empty/stub depth and segmentation.

---

## 6. Data flow

Step-by-step **current** flow for the live vision path:

1. User opens **`/vision/`** in the browser.
2. **`startCamera()`** runs; **`getUserMedia`** starts the video stream; video plays.
3. User enables **Sight Scan**; **`captureAndAnalyze`** runs.
4. Current video frame is drawn to **canvas** and exported as **JPEG data URL** (`frame_data`).
5. Browser sends **POST `/api/navigation/stream/`** with JSON body (`frame_data`, `text_prompt`).
6. **`NavigationStreamView`** validates `frame_data`, then calls **`analyze_frame_context`** with `run_vision_first=True`.
7. **`process_frame_vision_pipeline`** runs: YOLO detection → ByteTrack wrapper → depth stub → segmentation stub → **`metadata`** dict.
8. **`GeminiAnalyzer.analyze_scene`** sends **text prompts + JSON metadata** to Gemini; receives **`analysis_text`**.
9. **`generate_audio_feedback`** writes WAV under **`/tmp`** via pyttsx3 (if engine OK) or an empty file if not; returns **`audio_url`** path fragment `/media/...`.
10. **HTTP 200** JSON returns to the browser.
11. **`updateDynamicUI(metadata)`** renders boxes/alerts (Tailwind classes depend on detection data).
12. **`speechSynthesis`** speaks **`analysis_text`**; when utterance ends, the next **`captureAndAnalyze`** iteration is scheduled if scanning is still on.

---

## 7. Dependencies

From `requirements.txt` and code usage:

| Dependency | Role in this codebase |
|------------|------------------------|
| **Django** | Web framework, routing, templates, ORM, admin. |
| **djangorestframework** | `APIView`, `Response`, status codes for `/api/navigation/stream/`. |
| **django-filter** | Listed in `INSTALLED_APPS`; no custom usage surfaced in the analyzed views. |
| **python-dotenv** | `load_dotenv()` in `apps/core/services.py` for local env loading. |
| **celery** | Task decorators (`@shared_task`); Celery app in `sightra/celery.py`; broker/backend Redis in settings. |
| **redis** | Celery broker/result backend (per settings). |
| **google-generativeai** | Gemini client (`genai.configure`, `GenerativeModel`, `generate_content`). |
| **ultralytics** | YOLO loading and inference (`YOLO("yolo11n.pt")`). |
| **opencv-python-headless** | `cv2.imdecode` for base64 → image array. |
| **torch / torchvision** | Pulled in for ML stack compatibility (YOLO/vision ecosystem). |
| **transformers**, **numpy**, **soundfile** | Declared for audio/ML; **transcription path is stubbed** in `AudioService.transcribe_audio`. |
| **pyttsx3** | Offline TTS in `AudioService.save_to_speech`; may fail if system TTS backend (e.g. eSpeak) is missing. |

**Frontend CDNs (not in requirements.txt):** Tailwind CDN, Google Fonts, Material Symbols.

---

## 8. Limitations of current implementation

The following are **observable constraints** of the design and code as it exists (not recommendations):

- **Browser dependency:** The interactive camera and speech loop require a **modern browser** with **`getUserMedia`**, **canvas**, **`fetch`**, and **`speechSynthesis`**.
- **Gemini does not receive pixels:** Only **structured metadata** (mostly YOLO output) is sent; depth and segmentation are **stubs**, so the model lacks real depth/segmentation signal from this pipeline.
- **API key configuration:** Effective key for `genai.configure` comes from **`GEMINI_API_KEY` in the environment** (after `load_dotenv`). The **`GEMINI_API_KEY` in `settings.py`** is separate and is **not** what `GeminiAnalyzer` uses for `configure`.
- **Task decorators vs execution:** Navigation uses **synchronous** calls into task functions; **Redis/Celery workers** are not required for that request path to run, but **imports still load heavy models** (YOLO at worker/module import) when the vision task module is loaded.
- **Vision stubs:** **ZoeDepth** and **GroundedSAM** return **minimal or empty** data; **ByteTrack** is a **placeholder** (IDs from enumeration, not real multi-frame tracking).
- **Audio URL vs Django media:** Response includes **`/media/...`** URLs while **`settings.py` does not define `MEDIA_URL` / `MEDIA_ROOT` or static/media serving** for those files; files are written to **`/tmp`**. Clients using `audio_url` may not receive playable audio without additional deployment configuration.
- **CSRF:** The vision page’s **`fetch` POST does not send a CSRF token**; whether requests succeed depends on DRF authentication defaults and cookie/session behavior in deployment.
- **Security settings:** `DEBUG = True`, `ALLOWED_HOSTS = ["*"]`, and a **hardcoded `SECRET_KEY`** in `settings.py` are present as in the repository.
- **Home / voice / settings:** **No backend integration** for voice capture, history, or persisted settings; **settings** UI changes are **in-memory only** in the browser.
- **SDK deprecation:** Importing **`google.generativeai`** emits a **FutureWarning** that the package is deprecated in favor of **`google.genai`** (runtime behavior still uses the old package as written).
- **Performance / latency:** Each scan performs **YOLO inference** and a **Gemini API round trip** in the request path; sequential **`speechSynthesis`** gating controls how fast the loop repeats—documented as current behavior, not an optimization target here.

---

## File reference index (quick lookup)

| Concern | Primary files |
|---------|----------------|
| Routes | `sightra/sightra/urls.py`, `sightra/apps/navigation/urls.py` |
| Navigation API | `sightra/apps/navigation/views.py` |
| Gemini | `sightra/apps/core/services.py` |
| Frame pipeline | `sightra/apps/vision/tasks.py`, `sightra/apps/vision/services.py` |
| Orchestration | `sightra/apps/core/tasks.py` |
| TTS | `sightra/apps/audio/services.py`, `sightra/apps/audio/tasks.py` |
| Camera client | `sightra/templates/vision.html` |
| Celery wiring | `sightra/sightra/celery.py`, `sightra/sightra/__init__.py` |
| Dependencies | `sightra/requirements.txt` |

---

*Generated from repository analysis; reflects the codebase as documented above.*
