# Sightra — Privacy & Data Flow Audit

**Audit date:** 2026-10-17  
**Scope:** Django application under `sightra/` (verified from codebase inspection)  
**Status:** Engineering audit — not legal compliance certification

---

## 1. Executive summary

Sightra processes account credentials via **Supabase**, optional **UI preferences** in SQLite, **transient camera frames** for YOLO + Gemini-assisted narration, **browser-local** theme/a11y data, and **client-side** map/voice flows that may reach third-party services. Persistent interaction history and analytics are **not implemented** in the current codebase. This audit informed the privacy app (`apps/privacy`), consent enforcement on `/api/navigation/stream/`, and versioned legal content under `/legal/`.

---

## 2. Data inventory

| # | Category | Collected? | Stored persistently? | Location / flow | External recipients | Retention (as implemented) |
|---|----------|------------|----------------------|-----------------|---------------------|----------------------------|
| 1 | Account identity | Yes | Yes (partial) | Supabase Auth; `UserPreference.email`, session `sightra_supabase` | Supabase | Until account deletion |
| 2 | Email / contact | Yes | Yes | As above | Supabase | Provider + local prefs |
| 3 | Camera frames | Yes (feature use) | **No** (server DB/disk) | Browser → `POST /api/navigation/stream/` → OpenCV decode in memory | None for raw pixels; metadata to Gemini | Request lifetime |
| 4 | Voice / mic | Yes (browser) | No server upload in MVP | Web Speech API; LiveKit on connect pages | Browser vendor; LiveKit | Ephemeral |
| 5 | GPS / navigation | Yes (browser) | No backend store | `live-map.html` geolocation + Nominatim/OSRM | OSM, Nominatim, OSRM | In-page only |
| 6 | Prompts / AI text | Yes | No DB; in-process Gemini cache | `text_prompt` + YOLO metadata → Gemini | Google Gemini | Process + Google terms |
| 7 | A11y / language prefs | Yes | Yes (local + optional sync) | localStorage + `UserPreference` | None | Until user clears/deletes |
| 8 | Consent records | Yes (post-implementation) | Yes | `ConsentRecord`, `PrivacyProfile` | None | Until deletion request |
| 9 | Logs / cookies | Yes | Host-dependent | `sessionid`, `csrftoken`; server logs | Hosting provider | Session TTL / host policy |
| 10 | Third-party AI | Yes (metadata) | Per Google | `GeminiAnalyzer` | Google | Per API config |

---

## 3. Transient vs persistent (verified)

| Data | Transient | Persistent |
|------|-----------|------------|
| JPEG frame bytes | Yes (memory) | Not written to SQLite |
| YOLO boxes | Yes | No |
| Gemini reply | In-memory cache per worker | No |
| TTS WAV | `/tmp` file | No DB; cleanup not automated |
| OAuth tokens in URL | Seconds in browser | Then server session only |

---

## 4. Lawful basis & consent (for legal verification)

| Processing | Indicative basis | Consent mechanism in app |
|------------|------------------|---------------------------|
| Account login | Contract / legitimate interest | Terms + privacy notice ack |
| Live Vision | Consent + contract (verify with counsel) | Privacy onboarding + camera feature consent + OS camera permission |
| Maps GPS | Consent | Location feature consent + OS location permission |
| Optional history / research / AI training | Consent | Opt-in checkboxes (defaults off); features largely not active |
| Security logging | Legitimate interest | Documented in policy |

**Kenya DPA / ODPC:** Mapping must be confirmed by qualified Kenyan counsel before production claims.

---

## 5. Risks identified (pre-mitigation)

| Risk | Severity | Mitigation implemented / planned |
|------|----------|----------------------------------|
| Public vision API without login | High | Consent required on stream endpoint (403 without consent) |
| TTS text in logs | Medium | Log length only (`apps/audio/services.py`) |
| JWT unsigned fallback if JWKS missing | High | Document in compliance report; configure JWKS in prod |
| No automated `/tmp` audio cleanup | Low | Operations runbook item |
| International transfer to US AI/cloud | Medium | Policy disclosure + DPA/SCC action item |
| Placeholder legal contacts | Medium | `legal_config.py` placeholders |

---

## 6. Recommended follow-ups

1. Configure real contact/DPO details in `apps/privacy/legal_config.py`.  
2. Enable Supabase JWKS URL; remove unsigned JWT fallback for production.  
3. Require authentication for vision API if product policy allows.  
4. DPIA and ODPC registration as advised by counsel.  
5. Implement interaction history only if optional consent enabled and design documented.  
6. Scheduled cleanup of temp audio files.

---

## 7. Document control

| Version | Date | Notes |
|---------|------|-------|
| 1.0 | 2026-10-17 | Initial audit + privacy framework implementation |

Related: [compliance-verification-report.md](./compliance-verification-report.md), [../.docs/TECHNICAL_REPORT.md](../.docs/TECHNICAL_REPORT.md).
