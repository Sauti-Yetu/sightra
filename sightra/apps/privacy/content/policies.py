"""Version-controlled legal document bodies (HTML fragments)."""

from apps.privacy import legal_config as lc
from apps.privacy.constants import POLICY_EFFECTIVE_DATE, POLICY_VERSION


def _footer() -> str:
    return (
        f'<p class="legal-meta"><strong>Version:</strong> {POLICY_VERSION} · '
        f"<strong>Effective date:</strong> {POLICY_EFFECTIVE_DATE}</p>"
        '<p class="text-sm text-[var(--text-muted)]">This document describes current product behaviour '
        "as implemented in the Sightra codebase. It does not constitute legal advice or a claim of "
        "regulatory compliance. Qualified Kenyan counsel and ODPC guidance should be applied before "
        "relying on this text in production.</p>"
    )


def get_all_policies() -> dict[str, dict]:
    return {
        "privacy-policy": _privacy_policy(),
        "terms-of-use": _terms_of_use(),
        "ai-transparency": _ai_transparency(),
        "cookie-storage": _cookie_notice(),
    }


def get_policy(slug: str) -> dict | None:
    return get_all_policies().get(slug)


def _privacy_policy() -> dict:
    return {
        "slug": "privacy-policy",
        "title": "Privacy Policy",
        "sections": [
            {
                "heading": "Who we are",
                "body": (
                    f"<p><strong>{lc.OPERATOR_NAME}</strong> operates <strong>{lc.PRODUCT_NAME}</strong>, "
                    f"an assistive application for people who are blind or have low vision.</p>"
                    f"<p><strong>Contact:</strong> {lc.CONTACT_EMAIL}<br>"
                    f"<strong>Data protection contact:</strong> {lc.DPO_CONTACT}<br>"
                    f"<strong>Postal address:</strong> {lc.POSTAL_ADDRESS}<br>"
                    f"<strong>Registration (if applicable):</strong> {lc.REGISTRATION_NUMBER}</p>"
                ),
            },
            {
                "heading": "What this policy covers",
                "body": (
                    "<p>This policy explains how we process personal data when you use Sightra’s website "
                    "and signed-in features. It is based on our engineering audit of the current application "
                    "and may be updated when processing changes.</p>"
                ),
            },
            {
                "heading": "Categories of data we process",
                "body": (
                    "<ul>"
                    "<li><strong>Account data:</strong> email address and Supabase user identifier when you "
                    "register or sign in. Passwords are handled by Supabase; we do not store passwords in "
                    "our database.</li>"
                    "<li><strong>Session data:</strong> authentication tokens stored in a Django session cookie "
                    "to keep you signed in.</li>"
                    "<li><strong>Preferences:</strong> theme and accessibility settings you choose (stored in "
                    "browser local storage and, when signed in, synced to our database).</li>"
                    "<li><strong>Camera frames:</strong> when you use Live Vision, images are captured in your "
                    "browser and sent to our server for analysis. They are processed in memory and are "
                    "<strong>not</strong> saved to our database or disk by default.</li>"
                    "<li><strong>Environmental analysis:</strong> object labels and safety metadata from on-server "
                    "detection, plus short text guidance generated using Google Gemini from that metadata and "
                    "optional text prompts (raw camera images are not sent to Gemini in the current implementation).</li>"
                    "<li><strong>Location:</strong> if you use map features, your browser may request GPS coordinates "
                    "or you may enter place names. Map pages may contact third-party geocoding and routing services "
                    "from your browser; coordinates are not stored in our database by default.</li>"
                    "<li><strong>Voice:</strong> voice assistant features may use your device’s speech engine in the "
                    "browser. Live Connect may use real-time audio via LiveKit when you join a call.</li>"
                    "<li><strong>Consent records:</strong> your privacy choices and timestamps for accountability.</li>"
                    "<li><strong>Technical logs:</strong> server logs may include errors and operational messages. "
                    "We aim to avoid logging camera content; TTS generation should not log full scene descriptions.</li>"
                    "</ul>"
                ),
            },
            {
                "heading": "Purposes and lawful bases (subject to legal verification)",
                "body": (
                    "<p>For each activity, the appropriate lawful basis under the Kenya Data Protection Act "
                    "must be confirmed with qualified counsel. Indicative mapping:</p>"
                    "<ul>"
                    "<li>Providing account access and preferences — contract / legitimate interests.</li>"
                    "<li>Environmental analysis you request — contract and/or consent for camera processing, "
                    "depending on legal advice.</li>"
                    "<li>Security and fraud prevention — legitimate interests.</li>"
                    "<li>Optional history, research, or analytics — consent if enabled (off by default).</li>"
                    "</ul>"
                ),
            },
            {
                "heading": "Third parties",
                "body": (
                    "<ul>"
                    "<li><strong>Supabase</strong> — authentication (may process account data outside Kenya depending "
                    "on project region; review your Supabase data processing terms).</li>"
                    "<li><strong>Google (Gemini)</strong> — text generation from detection metadata and prompts.</li>"
                    "<li><strong>OpenStreetMap / Nominatim / OSRM</strong> (via browser on map pages) — map tiles, "
                    "search, and routing.</li>"
                    "<li><strong>LiveKit</strong> — real-time audio/video for volunteer connect when used.</li>"
                    "<li><strong>Hosting provider</strong> — application hosting (e.g. cPanel server).</li>"
                    "</ul>"
                ),
            },
            {
                "heading": "International transfers",
                "body": (
                    "<p>Some providers may process data outside Kenya. Where required, appropriate safeguards "
                    "(contractual clauses, adequacy decisions, or ODPC-approved mechanisms) must be implemented "
                    "before production reliance. This is an operational and legal action item.</p>"
                ),
            },
            {
                "heading": "Retention",
                "body": (
                    "<ul>"
                    "<li>Account preferences and consent records — until you delete them or close your account, "
                    "unless law requires longer retention.</li>"
                    "<li>Session cookies — typically up to two weeks unless configured otherwise.</li>"
                    "<li>Camera frames — transient (request processing only).</li>"
                    "<li>Server TTS files — may be written temporarily under system temp directories; cleanup "
                    "should be configured operationally.</li>"
                    "<li>Supabase and Google — governed by their respective retention settings and terms.</li>"
                    "</ul>"
                ),
            },
            {
                "heading": "Security",
                "body": (
                    "<p>We use HTTPS, session-based authentication, and environment-isolated secrets. No system "
                    "is perfectly secure. You are responsible for keeping your password and device secure.</p>"
                ),
            },
            {
                "heading": "Your rights",
                "body": (
                    "<p>Subject to Kenyan law, you may have rights to access, rectify, erase, restrict, object, "
                    "and port data, and to withdraw consent where processing is consent-based. Use "
                    "<a href=\"/legal/rights/\">Privacy rights &amp; data requests</a> in Settings or contact "
                    f"{lc.CONTACT_EMAIL}. You may lodge a complaint with the "
                    f'<a href="{lc.ODPC_URL}" rel="noopener">Office of the Data Protection Commissioner (ODPC)</a>.</p>'
                ),
            },
            {
                "heading": "Children",
                "body": (
                    "<p>Sightra is not directed at children without guardian involvement. If you believe a child "
                    "has provided personal data without appropriate authority, contact us to request deletion.</p>"
                ),
            },
        ],
        "footer": _footer(),
    }


def _terms_of_use() -> dict:
    return {
        "slug": "terms-of-use",
        "title": "Terms of Use",
        "sections": [
            {
                "heading": "Agreement",
                "body": (
                    f"<p>By using {lc.PRODUCT_NAME}, you agree to these Terms and our Privacy Policy. "
                    "If you do not agree, do not use the service.</p>"
                ),
            },
            {
                "heading": "Assistive tool — not a safety guarantee",
                "body": (
                    "<p>Sightra provides environmental information to support independence. It is "
                    "<strong>not</strong> a medical device, certified orientation aid, or substitute for "
                    "a white cane, guide dog, or human assistance. See the AI Transparency notice.</p>"
                ),
            },
            {
                "heading": "Acceptable use",
                "body": (
                    "<ul>"
                    "<li>Use Sightra lawfully and respect others’ privacy (avoid filming people without need or consent).</li>"
                    "<li>Do not attempt to break security, scrape the service, or misuse volunteer connect features.</li>"
                    "<li>Do not rely on Sightra as your sole means of avoiding hazards or traffic.</li>"
                    "</ul>"
                ),
            },
            {
                "heading": "Accounts",
                "body": (
                    "<p>You must provide accurate account information and keep credentials confidential. "
                    "Notify us if you suspect unauthorised access.</p>"
                ),
            },
            {
                "heading": "Availability",
                "body": (
                    "<p>The service may be interrupted for maintenance, network failures, or third-party outages "
                    "(AI APIs, maps, authentication). Features may change as the product evolves.</p>"
                ),
            },
            {
                "heading": "Intellectual property",
                "body": (
                    "<p>Sightra software, branding, and documentation are owned by or licensed to "
                    f"{lc.OPERATOR_NAME}. Open-source components remain under their respective licenses.</p>"
                ),
            },
            {
                "heading": "Third-party services",
                "body": (
                    "<p>Your use of integrated services (Supabase, Google, maps, LiveKit) is also subject to "
                    "their terms. We are not responsible for third-party acts or omissions beyond what law requires.</p>"
                ),
            },
            {
                "heading": "Limitation of liability",
                "body": (
                    "<p>To the fullest extent permitted by applicable law in {jurisdiction}, {operator} is not "
                    "liable for indirect, incidental, or consequential damages arising from use of Sightra, "
                    "including injury or property damage where environmental information was wrong or delayed. "
                    "Nothing in these Terms excludes liability that cannot be excluded under mandatory law "
                    "(including certain consumer rights where applicable).</p>".format(
                        jurisdiction=lc.JURISDICTION, operator=lc.OPERATOR_NAME
                    )
                ),
            },
            {
                "heading": "Governing law and disputes",
                "body": (
                    f"<p>These Terms are intended to be governed by the laws of {lc.JURISDICTION}, subject to "
                    "legal review. Disputes should first be raised via {contact}.</p>".format(
                        contact=lc.CONTACT_EMAIL
                    )
                ),
            },
        ],
        "footer": _footer(),
    }


def _ai_transparency() -> dict:
    return {
        "slug": "ai-transparency",
        "title": "AI Transparency & Safety Notice",
        "sections": [
            {
                "heading": "Automated analysis",
                "body": (
                    "<p>Sightra uses automated computer vision (YOLO object detection) and a large language model "
                    "(Google Gemini) to produce spoken and written guidance. Outputs are generated automatically "
                    "and may be wrong, incomplete, or delayed.</p>"
                ),
            },
            {
                "heading": "What can go wrong",
                "body": (
                    "<ul>"
                    "<li>People, vehicles, obstacles, signs, or surfaces may be missed or mislabelled.</li>"
                    "<li>Distance and position descriptions are approximate, not measurements.</li>"
                    "<li>Language may sound confident even when the system is uncertain.</li>"
                    "<li>Network or server delay may mean the environment changed before you hear guidance.</li>"
                    "</ul>"
                ),
            },
            {
                "heading": "Your safety responsibilities",
                "body": (
                    "<ul>"
                    "<li>Do not cross roads or enter hazardous areas based on Sightra alone.</li>"
                    "<li>Continue using your mobility training, cane, dog, and hearing.</li>"
                    "<li>Stop and seek human help when unsure.</li>"
                    "</ul>"
                ),
            },
            {
                "heading": "Human assistance (Live Connect)",
                "body": (
                    "<p>Volunteer or agent video calls are separate from automated AI. They may involve live "
                    "audio/video through LiveKit. Only enable when you understand who may join and how sessions "
                    "are moderated (operational policies apply).</p>"
                ),
            },
            {
                "heading": "External AI providers",
                "body": (
                    "<p>Gemini processes structured detection data and optional text prompts according to "
                    "Google’s terms and your API configuration. We do not use your data for public model "
                    "training unless you separately opt in to any future secondary-use programme (disabled by default).</p>"
                ),
            },
        ],
        "footer": _footer(),
    }


def _cookie_notice() -> dict:
    return {
        "slug": "cookie-storage",
        "title": "Cookies & Local Storage Notice",
        "sections": [
            {
                "heading": "What we use today",
                "body": (
                    "<p>We do not operate third-party advertising or analytics cookies in the current codebase.</p>"
                    "<ul>"
                    "<li><strong>sessionid</strong> (cookie) — essential Django session for sign-in.</li>"
                    "<li><strong>csrftoken</strong> (cookie) — essential security for form/API POST requests.</li>"
                    "<li><strong>sightra_theme / sightra_a11y</strong> (local storage) — your theme and accessibility choices.</li>"
                    "<li><strong>Service worker cache</strong> — offline shell for static pages; API responses are not cached.</li>"
                    "</ul>"
                ),
            },
            {
                "heading": "Optional storage",
                "body": (
                    "<p>If you enable optional analytics in Privacy settings in a future release, we will update "
                    "this notice before activation. Optional analytics are off by default.</p>"
                ),
            },
            {
                "heading": "Managing storage",
                "body": (
                    "<p>You can clear site data in your browser settings. Clearing cookies will sign you out.</p>"
                ),
            },
        ],
        "footer": _footer(),
    }
