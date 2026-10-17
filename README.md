# Sightra

**Sightra** is an AI-powered assistive web application for blind and visually impaired users. It combines live camera input, on-device/server-side object detection (YOLO26n), and Google Gemini narration to deliver hazard-first audio guidance, scene understanding, and companion features (voice, maps, volunteer connect).

**Organization:** [Sauti-Yetu](https://github.com/Sauti-Yetu)  
**Repository:** `https://github.com/Sauti-Yetu/sightra`  
**Production site:** [sightra.net](https://sightra.net) (cPanel deploy via `.cpanel.yml`)

For company technical reporting, governance, safety, and user manuals, see [`.docs/TECHNICAL_REPORT.md`](.docs/TECHNICAL_REPORT.md) and [`.docs/README.md`](.docs/README.md).

Privacy engineering audit and compliance gap analysis: [`docs/privacy-data-flow-audit.md`](docs/privacy-data-flow-audit.md), [`docs/compliance-verification-report.md`](docs/compliance-verification-report.md). In-app **Privacy & Legal** centre: `/legal/`.

---

## Table of contents

1. [Architecture overview](#architecture-overview)
2. [Repository layout](#repository-layout)
3. [Prerequisites](#prerequisites)
4. [Local development](#local-development)
5. [Environment variables](#environment-variables)
6. [Authentication (Supabase)](#authentication-supabase)
7. [Vision pipeline (YOLO + Gemini)](#vision-pipeline-yolo--gemini)
8. [Progressive Web App (PWA)](#progressive-web-app-pwa)
9. [Running tests](#running-tests)
10. [Training and custom weights](#training-and-custom-weights)
11. [Deployment](#deployment)
12. [Branching and contribution](#branching-and-contribution)
13. [Troubleshooting](#troubleshooting)
14. [License and contact](#license-and-contact)

---

## Architecture overview

```text
Browser (camera + UI)
    │  POST base64 frame + optional text_prompt
    ▼
/api/navigation/stream/  (NavigationStreamView)
    │
    ├─► YOLO26n (apps/vision) → tiers, distance bands, hazard_alert
    │
    ├─► Gemini (apps/core) → safety-first TTS-ready sentences
    │
    └─► pyttsx3 audio (apps/audio) → WAV URL in JSON response
```

- **Backend:** Django 5+ with Django REST Framework; SQLite by default.
- **Auth:** Supabase (email/password + Google OAuth); session cookies via `apps/accounts` (not Django `User` for primary identity).
- **Optional async:** Celery + Redis configured in settings; main vision path is synchronous for low-latency HTTP responses.

---

## Repository layout

```text
sightra-1/                    # Git root
├── README.md                 # This file
├── .cpanel.yml               # cPanel Git deploy copy tasks
├── .docs/                    # Technical reporting & manuals (company)
└── sightra/                  # Django project root (run commands here)
    ├── manage.py
    ├── requirements.txt
    ├── .env.example          # Copy to .env — never commit .env
    ├── sightra/              # Project settings, urls, wsgi
    ├── apps/
    │   ├── accounts/         # Supabase auth, middleware, preferences
    │   ├── core/             # GeminiAnalyzer, frame analysis orchestration
    │   ├── vision/           # YOLO detector, priorities, hazard logic
    │   ├── navigation/       # Live map + /api/navigation/stream/
    │   ├── audio/            # TTS feedback
    │   ├── settings/         # User settings API
    │   └── volunteer/        # LiveKit token stub / connect flows
    ├── templates/            # Server-rendered pages (landing, vision, etc.)
    ├── static/               # CSS, JS, PWA manifest, service worker
    ├── models/weights/       # yolo26n.pt (committed), optional fine-tunes
    └── ml/vision/            # Train/validate/download scripts
```

---

## Prerequisites

| Requirement | Notes |
|-------------|--------|
| **Python** | **3.10 – 3.12 recommended** for `torch` / `ultralytics`. Python 3.14+ may fail dependency resolution. |
| **pip** | Virtual environment strongly recommended |
| **Redis** | Only if running Celery workers (optional for MVP) |
| **Supabase project** | Auth URL, anon/publishable key, JWT/JWKS |
| **Google AI API key** | Gemini (`GEMINI_API_KEY`) |

---

## Local development

```bash
git clone https://github.com/Sauti-Yetu/sightra.git
cd sightra/sightra          # Django project directory

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env        # Fill in secrets locally

python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Open `http://127.0.0.1:8000/` for the landing page. Sign in at `/signin/` or `/signup/`. Live vision: `/vision/` (requires login).

**Admin (optional):** `python manage.py createsuperuser` then `/admin/`.

---

## Environment variables

Copy `sightra/.env.example` to `sightra/.env`. Never commit `.env`.

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes (vision narration) | Google Generative AI key |
| `SUPABASE_URL` | Yes (auth) | e.g. `https://xxxx.supabase.co` |
| `SUPABASE_PUBLISHABLE_KEY` | Yes | Anon/publishable key |
| `SUPABASE_SECRET_KEY` | Server-side ops | Service role (keep server-only) |
| `SUPABASE_JWKS_URL` | Recommended | JWT verification (defaults derived from URL if omitted) |
| `YOLO_MODEL_PATH` | No | Default `models/weights/yolo26n.pt` |
| `YOLO_IMGSZ` | No | Inference size (default `512`) |
| `YOLO_CONF` | No | Confidence threshold (default `0.35`) |
| `YOLO_MAX_DET` | No | Max boxes per frame |
| `YOLO_IOU` | No | NMS IoU |
| `SIGHTTRA_REQUIRE_LOGIN` | No | `true` forces login for all non-public routes |
| `DJANGO_DEBUG` | Dev only | Use `False` in production |

Production must also set a strong `SECRET_KEY` and `DEBUG=False` in Django settings (see deployment checklist in `.docs/TECHNICAL_REPORT.md`).

---

## Authentication (Supabase)

- **Middleware:** `SupabaseAuthMiddleware` sets `request.sightra_user`; `LoginRequiredMiddleware` guards app routes.
- **Public:** `/`, `/signin/`, `/signup/`, `/auth/*`, static, PWA assets, most `/api/*` except account auth.
- **Protected:** `/dashboard`, `/vision/`, `/live-map/`, `/voice_assistant/`, `/live-call/`, `/sightra-connect/`, `/settings/`.

**Email/password:** Forms POST to `/api/accounts/auth/signin/` and `/signup/`.

**Google OAuth:** `/auth/google/` → Supabase authorize → `/auth/callback/` → `/api/accounts/auth/oauth/`.

**Supabase dashboard (required redirects):**

- Site URL: production and `http://127.0.0.1:8000` for local dev
- Redirect URLs: `https://sightra.net/auth/callback/`, `http://127.0.0.1:8000/auth/callback/`
- **Google OAuth:** Supabase → Authentication → Providers → Google — paste Google Cloud **Client ID** and **Client secret** (not in git). Enable the provider for the same Supabase project as `SUPABASE_URL`.
- **Email/password testing:** In Supabase → Authentication → Providers → **Email**, disable **Confirm email** if you want immediate sign-in after signup. Rate limits on auth emails are enforced by Supabase (not Django); wait or adjust Auth settings if you see “email rate limit”.
- **Keys:** Use `SUPABASE_PUBLISHABLE_KEY` (`sb_publishable_…`) and `SUPABASE_SECRET_KEY` (`sb_secret_…`) from the Supabase API settings. Set `SUPABASE_JWKS_URL` or leave empty to auto-derive from `SUPABASE_URL`.

**macOS SSL:** HTTP client uses `certifi` for Supabase HTTPS (`apps/accounts/services/supabase_client.py`).

---

## Vision pipeline (YOLO + Gemini)

1. Client captures a frame (base64) and POSTs to **`POST /api/navigation/stream/`** with `frame_data`, optional `text_prompt`, optional `frame_id`.
2. **`process_frame_vision_pipeline`** runs YOLO26n, enriches detections (`apps/vision/priorities.py`: tier, distance band, position, `blocks_path`).
3. **`build_hazard_alert`** may prepend urgent spoken cues.
4. **`GeminiAnalyzer`** (`gemini-3.1-flash-lite-preview`) synthesizes 1–3 short sentences with hazard-first rules.
5. **`generate_audio_feedback`** returns `analysis_text`, `audio_url`, `metadata`, `warnings`, `hazard_alert`.

If Ultralytics fails to load (missing deps or bad path), Gemini still runs but bounding-box metadata may be empty—treat as degraded mode.

Details: [`sightra/ml/vision/README.md`](sightra/ml/vision/README.md), [`sightra/models/README.md`](sightra/models/README.md).

---

## Progressive Web App (PWA)

- **Manifest:** `/manifest.webmanifest` (served via Django view)
- **Service worker:** `/sw.js` — offline shell for `/offline/`
- **Install prompt:** partial in templates; icons under `static/`
- **Accessibility:** high-contrast themes, sidebar, a11y panel partial (`templates/partials/a11y_panel.html`)

After static changes: ensure deploy copies `static/` (see `.cpanel.yml`).

---

## Running tests

From `sightra/`:

```bash
python manage.py test apps.vision.tests_priorities apps.vision.tests_models
```

---

## Training and custom weights

```bash
cd sightra/ml/vision
pip install -r ../../requirements.txt
python download_datasets.py    # coco128 smoke set
python validate.py --device cpu
python train.py --mobility      # or see README for full args
```

Fine-tuned weights: `models/weights/sightra_yolo26n.pt` — set `YOLO_MODEL_PATH` accordingly.

---

## Deployment

### cPanel (current production path)

`.cpanel.yml` copies `apps/`, `templates/`, `static/`, `sightra/`, `public/`, `manage.py`, and `requirements.txt` into the host deploy path.

**Post-deploy on server:**

1. Install Python dependencies (`pip install -r requirements.txt`).
2. Set environment variables (panel or `.env` outside git).
3. `python manage.py migrate`
4. Collect/serve static files per host configuration.
5. Restart WSGI/Passenger process.

Ensure **`models/weights/yolo26n.pt`** is present on the server (included in repo under `sightra/models/weights/`).

### Render / other hosts

- Bind to `0.0.0.0:$PORT` if using Render web services.
- Filesystem is ephemeral on free tiers—do not rely on local SQLite or generated audio persisting across restarts without attached storage.
- See Render platform notes in workspace rules and `.docs/TECHNICAL_REPORT.md`.

---

## Branching and contribution

1. Branch from `main`: `feat/<short-description>` or `fix/<issue>`.
2. Keep Django app changes under `sightra/`; update `.docs` when behavior, safety, or compliance-relevant logic changes.
3. Do not commit secrets, `.env`, or large datasets (`ml/vision/datasets/`, `runs/` are gitignored).
4. Open a PR against `main`; ensure vision priority tests pass.
5. Coordinate Supabase redirect URL updates when adding new deployment domains.

---

## Troubleshooting

| Symptom | Likely cause | Action |
|---------|----------------|--------|
| Sign-up SSL / certificate errors | CA bundle on macOS | Ensure `certifi` installed; restart server |
| No bounding boxes on vision | YOLO not loaded | Check logs, Python version, `ultralytics`, `YOLO_MODEL_PATH` |
| Gemini generic error message | Missing/invalid `GEMINI_API_KEY` | Set key in `.env` |
| Redirect loop on login | Supabase misconfig | Verify callback URLs and cookies |
| Slow frames | CPU inference + Gemini | Lower `YOLO_IMGSZ`, rate limits in `GeminiAnalyzer` |
| 401 on protected pages | No session | Sign in; check middleware paths |

---

## License and contact

MIT License — see [LICENSE](LICENSE).

Issues and internal support: GitHub Issues on **Sauti-Yetu/sightra** or your team channel.

**Documentation index:** [`.docs/README.md`](.docs/README.md)
