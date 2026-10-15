# Sightra — Operations Runbook

For DevOps and on-call engineers deploying and operating Sightra.

---

## 1. Service overview

| Item | Value |
|------|-------|
| App type | Django WSGI |
| Project path on server | `/home/sightran/sightra-main/sightra/` (per `.cpanel.yml`) |
| Deploy trigger | cPanel Git deploy + `.cpanel.yml` copy tasks |
| Default DB | SQLite (`db.sqlite3`) — back up on persistent disk |

---

## 2. Deploy procedure (cPanel)

1. Merge approved changes to `main`.
2. Trigger Git pull / deploy on host.
3. Verify `.cpanel.yml` copied: `apps/`, `templates/`, `static/`, `sightra/`, `manage.py`, `requirements.txt`.
4. SSH or terminal on host:
   ```bash
   cd /home/sightran/sightra-main/sightra/
   pip install -r requirements.txt
   python manage.py migrate --noinput
   ```
5. Confirm `models/weights/yolo26n.pt` exists.
6. Restart Python/Passenger application.
7. Smoke test: `/`, `/signin/`, authenticated `/vision/`, one POST to `/api/navigation/stream/`.

---

## 3. Environment variables (production)

Required for full functionality:

- `GEMINI_API_KEY`
- `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_SECRET_KEY` (server)
- `SUPABASE_JWKS_URL` (if not auto-derived)

Optional tuning:

- `YOLO_MODEL_PATH`, `YOLO_IMGSZ`, `YOLO_CONF`, `YOLO_MAX_DET`, `YOLO_IOU`
- `SIGHTTRA_REQUIRE_LOGIN=true` to lock down public browsing

**Never** log env values. Rotate keys if exposed.

---

## 4. Health checks

| Check | Command / action |
|-------|------------------|
| Django up | `curl -I https://sightra.net/` |
| Static manifest | `curl -I https://sightra.net/manifest.webmanifest` |
| YOLO load | Application log line: `YoloObjectDetector ready` |
| Gemini | Trigger vision frame; no `Gemini API error` in logs |
| Auth | Sign-in flow completes; cookie set |

---

## 5. Logs and common errors

| Log message | Meaning | Action |
|-------------|---------|--------|
| `Failed to load YOLO` | ultralytics/torch/weights path | Fix Python version (3.10–3.12), reinstall deps, verify weights path |
| `Gemini API error` | Key, quota, network | Verify `GEMINI_API_KEY`, Google Cloud status |
| Supabase SSL errors | CA bundle | Ensure `certifi` installed |
| `Supabase is not configured` | Missing URL/key | Set env vars |

---

## 6. Incident response

### 6.1 Severity guide

- **SEV1:** Production down or auth totally broken
- **SEV2:** Vision broken for all users (YOLO + Gemini fail)
- **SEV3:** Partial degradation (Gemini only), workaround exists (hazard strings from YOLO metadata if enabled)

### 6.2 Secret compromise

1. Revoke leaked key in Supabase / Google Cloud immediately.
2. Issue new keys; update host env.
3. Restart app.
4. Force sign-out all users if session secret compromised (rotate Django `SECRET_KEY` invalidates sessions).
5. Document in internal incident log.

### 6.3 Rollback

1. Revert git commit on `main` or redeploy previous tag.
2. Run migrate only if backward-compatible.
3. Restore `db.sqlite3` backup if migration failed.

---

## 7. Backup and restore

- **SQLite:** nightly copy of `db.sqlite3` to durable storage
- **User auth:** Supabase dashboard backups per project plan
- **Weights:** in git; fine-tuned weights on server should be copied to object storage

---

## 8. Scaling notes

- Sync vision endpoint blocks worker under load—use multiple workers + GPU or queue-based architecture for high traffic.
- Redis required only if enabling Celery workers.
- On Render: bind `0.0.0.0:$PORT`; use managed Postgres instead of SQLite for multi-instance.

---

## 9. Related documentation

- [TECHNICAL_REPORT.md](./TECHNICAL_REPORT.md)
- [README.md](../README.md)
