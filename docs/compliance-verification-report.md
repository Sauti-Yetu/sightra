# Sightra — Compliance Verification Report

**Organisation:** Sauti Yetu Assistive Venture  
**Product:** Sightra  
**Report date:** 2026-10-17  
**Report type:** Engineering & governance gap analysis (not legal opinion)

---

## Disclaimer

This report documents **technical and operational safeguards implemented in software** and **outstanding items** for legal and regulatory review. It **does not** state that Sightra is compliant with the Kenya Data Protection Act, ODPC requirements, or any other law. Final compliance determination requires qualified **Kenyan legal counsel** and engagement with the **Office of the Data Protection Commissioner (ODPC)** where applicable.

---

## 1. Implemented controls (engineering)

| Control | Implementation | Evidence |
|---------|----------------|----------|
| Privacy & legal centre | `/legal/*` pages from versioned `apps/privacy/content/policies.py` | Routes in `sightra/urls.py` |
| Consent management | `ConsentRecord`, `PrivacyProfile`, APIs under `/api/privacy/` | `apps/privacy/` |
| Onboarding modal | Required privacy notice + core processing before optional choices | `partials/privacy_onboarding_modal.html`, `privacy-consent.js` |
| Granular optional consent | Separate flags; default deny for history, research, AI training, analytics | Onboarding + settings |
| Camera processing gate | Server 403 without notice + camera consent | `NavigationStreamView` |
| User data export | `GET/POST /api/privacy/export/` (authenticated) | `api_data_export` |
| Account data deletion (app DB) | `POST /api/privacy/delete-account-data/` | Deletes prefs + consent; optional Supabase admin delete |
| AI transparency | Dedicated `/legal/ai-transparency/` | Policy content |
| Cookie/storage disclosure | `/legal/cookie-storage/` | Matches actual localStorage + cookies |
| Reduced sensitive logging | TTS logs character count only | `apps/audio/services.py` |
| Public legal routes | Accessible without login | Middleware `_PUBLIC_PREFIXES` |

---

## 2. Accessibility of privacy UX

| Requirement | Status |
|-------------|--------|
| Keyboard-operable onboarding form | Implemented (native controls) |
| Screen reader labels on modal | `role="dialog"`, `aria-labelledby` |
| Plain language headings in policies | Structured sections |
| Links from settings, signup, footer | Implemented |

**Outstanding:** Formal WCAG 2.2 audit not performed.

---

## 3. Responsible AI disclosures

| Topic | Disclosed to users? | Engineering note |
|-------|---------------------|------------------|
| Automated vision + LLM | Yes | AI transparency page |
| Error / delay / omission risk | Yes | Terms + AI notice |
| Not a safety-critical system | Yes | Multiple documents |
| Gemini as processor | Yes | Privacy policy |
| Human Live Connect | Yes | Separate mention |
| No default model training on user data | Yes | Opt-in only; not active |

---

## 4. Outstanding legal & operational requirements

| Item | Owner | Priority |
|------|-------|----------|
| Replace `[CONFIGURE: …]` placeholders in `legal_config.py` | Product / legal | **Blocker for production legal sign-off** |
| Confirm lawful basis per processing activity | Kenyan counsel | High |
| ODPC registration / DPC appointment if required | Legal | High |
| Cross-border transfer mechanisms (Supabase region, Google) | Legal + DPO | High |
| Privacy impact assessment (DPIA) | Legal + engineering | High |
| Terms & policy review by counsel | Legal | High |
| Incident response & breach notification playbook | Operations | Medium |
| `/tmp` audio retention & disk hygiene | DevOps | Medium |
| Authenticate vision API (optional product decision) | Product + engineering | Medium |
| Disable JWT unsigned fallback in production | Engineering | High |
| Volunteer / LiveKit moderation & privacy policy | Product | Medium |
| Children / guardian policy operational process | Support | Medium |
| Insurance / liability review for assistive claims | Legal | Medium |

---

## 5. User rights workflow

| Right | In-app path | Limitation |
|-------|-------------|------------|
| Access | Export JSON at `/legal/rights/` | Server-held data only |
| Erasure | Delete account data button | Supabase deletion needs service key or manual step |
| Rectification | Settings / preferences | Email changes via Supabase |
| Withdraw consent | `/settings/privacy/` | Feature-specific |
| Portability | JSON export | Partial |
| Complaint to ODPC | Linked in policies | User-directed |

---

## 6. Testing performed

- `apps.privacy.tests` — onboarding API  
- Existing vision priority tests unchanged  

**Recommended:** Integration tests for 403 consent on navigation stream; penetration test before high-risk deployment.

---

## 7. Version alignment

| Artifact | Version |
|----------|---------|
| Policy bundle | `2026.10.1` (`apps/privacy/constants.py`) |
| This report | 1.0 |

---

## 8. Sign-off placeholders

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Engineering lead | | | |
| Privacy / DPO | | | |
| Legal counsel (Kenya) | | | |
