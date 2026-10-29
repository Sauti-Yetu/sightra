"""Version-controlled legal document bodies (HTML fragments)."""

from apps.privacy import legal_config as lc
from apps.privacy.constants import (
    POLICY_ALIASES,
    POLICY_EFFECTIVE_DATE,
    POLICY_SLUG_COOKIES,
    POLICY_SLUG_LICENSES,
    POLICY_SLUG_PRIVACY,
    POLICY_SLUG_REFUND,
    POLICY_SLUG_TERMS,
    POLICY_SLUG_THIRD_PARTIES,
    POLICY_VERSION,
)


def _footer() -> str:
    return (
        f'<p class="legal-meta"><strong>Version:</strong> {POLICY_VERSION} · '
        f"<strong>Effective date:</strong> {POLICY_EFFECTIVE_DATE}</p>"
        '<p class="text-sm text-[var(--text-muted)]">This document describes current product behaviour '
        "as implemented in the Sightra codebase. It is not legal advice and is not a claim that the "
        "product is certified under any accessibility, medical, or data-protection regime. Qualified "
        f"counsel in {lc.JURISDICTION} should review this text before you rely on it.</p>"
    )


def get_all_policies() -> dict[str, dict]:
    return {
        POLICY_SLUG_PRIVACY: _privacy_policy(),
        POLICY_SLUG_TERMS: _terms_of_service(),
        "ai-transparency": _ai_transparency(),
        POLICY_SLUG_COOKIES: _cookie_policy(),
        POLICY_SLUG_REFUND: _refund_policy(),
        POLICY_SLUG_THIRD_PARTIES: _third_party_services(),
        POLICY_SLUG_LICENSES: _licenses(),
    }


def get_policy(slug: str) -> dict | None:
    canonical = POLICY_ALIASES.get(slug, slug)
    return get_all_policies().get(canonical)


def _privacy_policy() -> dict:
    return {
        "slug": POLICY_SLUG_PRIVACY,
        "title": "Privacy Policy",
        "sections": [
            {
                "heading": "Who we are",
                "body": (
                    f"<p><strong>{lc.OPERATOR_NAME}</strong> operates <strong>{lc.PRODUCT_NAME}</strong> "
                    f"({lc.WEBSITE_URL}), an assistive application for people who are blind or have low vision.</p>"
                    f"<p><strong>Contact:</strong> {lc.CONTACT_EMAIL}<br>"
                    f"<strong>Data protection contact:</strong> {lc.DPO_CONTACT}<br>"
                    f"<strong>Support:</strong> {lc.SUPPORT_EMAIL}<br>"
                    f"<strong>Postal address:</strong> {lc.postal_address_display()}<br>"
                    f"<strong>Registration:</strong> {lc.registration_display()}<br>"
                    f"<strong>Governing law (intended):</strong> {lc.JURISDICTION}</p>"
                ),
            },
            {
                "heading": "What this policy covers",
                "body": (
                    "<p>This policy explains how we process personal data when you use Sightra’s website "
                    "and signed-in features. It is based on an engineering audit of the current application "
                    "and is updated when processing changes.</p>"
                ),
            },
            {
                "heading": "Data minimisation — what we do not collect",
                "body": (
                    "<p>We collect only what is needed to create an account and run features you choose:</p>"
                    "<ul>"
                    "<li>We do not ask for your legal name, phone number, date of birth, national ID, or home address at sign-up.</li>"
                    "<li>We do not run advertising networks or sell personal data.</li>"
                    "<li>Camera frames are processed in memory for Live Vision and are not saved to our database.</li>"
                    "<li>Optional analytics, research, and AI-training uses are off unless you opt in, and those product features are not active in the current build.</li>"
                    "</ul>"
                ),
            },
            {
                "heading": "Categories of data we process",
                "body": (
                    "<ul>"
                    "<li><strong>Account data:</strong> email address and Supabase user identifier when you "
                    "register or sign in. Passwords are handled by Supabase; we do not store passwords in "
                    "our database.</li>"
                    "<li><strong>Session data:</strong> authentication tokens in a Django session cookie "
                    "to keep you signed in.</li>"
                    "<li><strong>Preferences:</strong> theme and accessibility settings (browser storage and, "
                    "when signed in, our database).</li>"
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
                    "<li><strong>Consent and rights requests:</strong> your privacy choices, cookie choices, "
                    "age/guardian attestation, and deletion or unsubscribe requests.</li>"
                    "<li><strong>Technical logs:</strong> server logs may include errors and operational messages. "
                    "We aim to avoid logging camera content.</li>"
                    "</ul>"
                ),
            },
            {
                "heading": "Purposes and lawful bases",
                "body": (
                    f"<p>For each activity, the appropriate lawful basis under the {lc.JURISDICTION} Data Protection Act "
                    "must be confirmed with qualified counsel. Indicative mapping:</p>"
                    "<ul>"
                    "<li>Providing account access and preferences — contract / legitimate interests.</li>"
                    "<li>Environmental analysis you request — contract and/or consent for camera processing.</li>"
                    "<li>Security and fraud prevention — legitimate interests.</li>"
                    "<li>Optional history, research, analytics, or marketing email — consent (off by default).</li>"
                    "<li>Children’s data — parental or guardian consent (see Children, below).</li>"
                    "</ul>"
                ),
            },
            {
                "heading": "Cookies",
                "body": (
                    '<p>See the <a href="/legal/cookie-policy/">Cookie Policy</a>. Essential cookies keep you signed in '
                    "and protect forms. Optional cookies are off until you accept them in the cookie banner.</p>"
                ),
            },
            {
                "heading": "Third parties",
                "body": (
                    '<p>A current list is published in <a href="/legal/third-party-services/">Third-party services</a>. '
                    "Main processors:</p>"
                    "<ul>"
                    "<li><strong>Supabase</strong> — authentication.</li>"
                    "<li><strong>Google (Gemini, Fonts, optional OAuth)</strong> — narration, webfonts, sign-in.</li>"
                    "<li><strong>OpenStreetMap / Nominatim / OSRM</strong> — maps, search, and routing in the browser.</li>"
                    "<li><strong>LiveKit</strong> — real-time audio/video for volunteer connect when used.</li>"
                    "<li><strong>Hosting provider</strong> — application hosting.</li>"
                    "</ul>"
                ),
            },
            {
                "heading": "International transfers",
                "body": (
                    f"<p>Some providers may process data outside {lc.JURISDICTION}. Where required, appropriate safeguards "
                    "must be implemented. This is an operational and legal action item for the operator.</p>"
                ),
            },
            {
                "heading": "Retention",
                "body": (
                    "<ul>"
                    "<li>Account preferences and consent records — until you delete them or close your account, "
                    "unless law requires longer retention.</li>"
                    "<li>Data subject requests — until handled, then as needed for legal accountability.</li>"
                    "<li>Session cookies — typically up to two weeks unless configured otherwise.</li>"
                    "<li>Camera frames — transient (request processing only).</li>"
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
                    f"<p>Subject to {lc.JURISDICTION} law, you may have rights to access, rectify, erase, restrict, object, "
                    "and port data, and to withdraw consent where processing is consent-based. Use "
                    '<a href="/legal/rights/">Privacy rights &amp; data requests</a> or email '
                    f'{lc.CONTACT_EMAIL}. You may lodge a complaint with the '
                    f'<a href="{lc.ODPC_URL}" rel="noopener">Office of the Data Protection Commissioner (ODPC)</a>.</p>'
                ),
            },
            {
                "heading": "Children and parental consent",
                "body": (
                    f"<p>Sightra is intended for users aged {lc.MINIMUM_AGE} or older, or younger users with a parent "
                    "or guardian’s consent. We do not knowingly collect extra children’s data. At sign-up you must "
                    f"confirm you are {lc.MINIMUM_AGE}+ or that a parent/guardian consents.</p>"
                    "<p>A parent or guardian may:</p>"
                    "<ul>"
                    "<li>Submit consent or withdraw it at "
                    '<a href="/legal/parental-consent/">Parental consent</a>.</li>'
                    "<li>Request deletion of a child’s data via "
                    '<a href="/legal/rights/">data deletion request</a>.</li>'
                    "</ul>"
                    f"<p>If you believe a child provided personal data without authority, contact {lc.CONTACT_EMAIL}.</p>"
                ),
            },
            {
                "heading": "Email and unsubscribe",
                "body": (
                    "<p>Account confirmation and security messages may be sent by our authentication provider. "
                    "Optional product emails are off unless you opt in. Every optional email includes an "
                    '<a href="/legal/unsubscribe/">unsubscribe</a> link. You can also email '
                    f"{lc.CONTACT_EMAIL} with the subject line Unsubscribe.</p>"
                ),
            },
        ],
        "footer": _footer(),
    }


def _terms_of_service() -> dict:
    return {
        "slug": POLICY_SLUG_TERMS,
        "title": "Terms of Service",
        "sections": [
            {
                "heading": "Agreement",
                "body": (
                    f"<p>By using {lc.PRODUCT_NAME} you agree to these Terms of Service and our "
                    '<a href="/legal/privacy-policy/">Privacy Policy</a>. If you do not agree, do not use the service. '
                    "These Terms were previously titled Terms of Use; that URL still works.</p>"
                ),
            },
            {
                "heading": "Who may use Sightra",
                "body": (
                    f"<p>You must be at least {lc.MINIMUM_AGE} years old, or have verifiable consent from a parent "
                    "or guardian, to create an account. See Parental consent in the Privacy Policy.</p>"
                ),
            },
            {
                "heading": "Assistive tool — not a safety or medical guarantee",
                "body": (
                    "<p>Sightra provides environmental information to support independence. It is "
                    "<strong>not</strong> a medical device, certified orientation and mobility aid, or a substitute for "
                    "a white cane, guide dog, or human assistance. Outputs can be wrong, incomplete, or delayed. "
                    "Do not rely on Sightra as your only means of avoiding hazards or traffic. "
                    'See the <a href="/legal/ai-transparency/">AI Transparency</a> notice.</p>'
                ),
            },
            {
                "heading": "No hidden fees",
                "body": (
                    "<p>Sightra is currently offered at no charge. There are no in-app purchases, subscriptions, "
                    "or surprise fees in the current product. If paid plans are introduced later, prices will be "
                    "shown before you pay. "
                    'See the <a href="/legal/refund-policy/">Refund Policy</a>.</p>'
                ),
            },
            {
                "heading": "Acceptable use",
                "body": (
                    "<ul>"
                    "<li>Use Sightra lawfully and respect others’ privacy (avoid filming people without need or consent).</li>"
                    "<li>Do not attempt to break security, scrape the service, or misuse volunteer connect features.</li>"
                    "<li>Do not post fake reviews, impersonate volunteers, or misrepresent the service.</li>"
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
                "heading": "Intellectual property, fonts, and images",
                "body": (
                    "<p>Sightra software, branding, and documentation are owned by or licensed to "
                    f"{lc.OPERATOR_NAME}. Open-source components remain under their respective licenses. "
                    'Font and image attributions are listed in <a href="/legal/licenses/">Licenses</a>.</p>'
                ),
            },
            {
                "heading": "Third-party services",
                "body": (
                    '<p>Your use of integrated services is also subject to their terms. See '
                    '<a href="/legal/third-party-services/">Third-party services</a>. We are not responsible for '
                    "third-party acts or omissions beyond what law requires.</p>"
                ),
            },
            {
                "heading": "Limitation of liability",
                "body": (
                    f"<p>To the fullest extent permitted by applicable law in {lc.JURISDICTION}, {lc.OPERATOR_NAME} is not "
                    "liable for indirect, incidental, or consequential damages arising from use of Sightra, "
                    "including injury or property damage where environmental information was wrong or delayed. "
                    "Nothing in these Terms excludes liability that cannot be excluded under mandatory law "
                    "(including certain consumer rights where applicable).</p>"
                ),
            },
            {
                "heading": "Governing law and disputes",
                "body": (
                    f"<p>These Terms are intended to be governed by the laws of {lc.JURISDICTION}, subject to "
                    f"legal review. Disputes should first be raised via {lc.CONTACT_EMAIL}.</p>"
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
                "heading": "Unsupported claims we do not make",
                "body": (
                    "<p>We do not claim that Sightra restores sight, replaces professional orientation and mobility "
                    "training, guarantees safety, or meets a medical-device standard. Any on-screen detection "
                    "confidence value is a model estimate for that frame, not a promise of accuracy.</p>"
                ),
            },
            {
                "heading": "Human assistance (Live Connect)",
                "body": (
                    "<p>Volunteer or agent video calls are separate from automated AI. They may involve live "
                    "audio/video through LiveKit. Availability of volunteers is not guaranteed.</p>"
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


def _cookie_policy() -> dict:
    return {
        "slug": POLICY_SLUG_COOKIES,
        "title": "Cookie Policy",
        "sections": [
            {
                "heading": "How we use cookies and similar storage",
                "body": (
                    "<p>This Cookie Policy explains cookies, local storage, and similar technologies on Sightra. "
                    "It sits alongside the Privacy Policy. A cookie banner asks for optional storage; essential "
                    "cookies are required for the site to work.</p>"
                ),
            },
            {
                "heading": "Essential (always on)",
                "body": (
                    "<ul>"
                    "<li><strong>sessionid</strong> — keeps you signed in.</li>"
                    "<li><strong>csrftoken</strong> — protects forms and APIs from cross-site request forgery.</li>"
                    "<li><strong>sightra_theme / sightra_a11y</strong> (local storage) — theme and accessibility choices you make.</li>"
                    "<li><strong>sightra_cookie_choice</strong> (local storage) — remembers your cookie banner decision.</li>"
                    "<li><strong>Service worker cache</strong> — offline shell for static pages; API responses are not cached.</li>"
                    "</ul>"
                    "<p>These are strictly necessary. The banner cannot turn them off without breaking sign-in and security.</p>"
                ),
            },
            {
                "heading": "Optional (off until you accept)",
                "body": (
                    "<p>Optional analytics cookies and similar trackers are <strong>not used</strong> in the current "
                    "codebase. If you tap “Accept optional”, we record that choice so we may enable privacy-respecting "
                    "analytics later and will update this policy first. “Reject optional” is always as easy as accept. "
                    "There is no pre-ticked marketing box.</p>"
                ),
            },
            {
                "heading": "Third-party requests that are not advertising cookies",
                "body": (
                    "<p>To render the interface we currently load Tailwind CSS and Google Fonts / Material Symbols from "
                    "public CDNs. Those requests may expose your IP address to those providers. They are treated as "
                    "functional, not advertising. See Third-party services.</p>"
                ),
            },
            {
                "heading": "Managing cookies",
                "body": (
                    '<p>Use the cookie banner, <a href="/settings/privacy/">Privacy settings</a> when signed in, '
                    "or your browser settings. Clearing cookies will sign you out.</p>"
                ),
            },
        ],
        "footer": _footer(),
    }


def _refund_policy() -> dict:
    return {
        "slug": POLICY_SLUG_REFUND,
        "title": "Refund Policy",
        "sections": [
            {
                "heading": "Current product is free",
                "body": (
                    f"<p>{lc.PRODUCT_NAME} is currently provided free of charge. There are no paid subscriptions, "
                    "in-app purchases, or hidden fees in the software as shipped. If you were not charged by us, "
                    "there is nothing to refund.</p>"
                ),
            },
            {
                "heading": "If paid features are added later",
                "body": (
                    "<p>Before any paid plan goes live we will show the price, billing period, and what you get. "
                    "We will not add surprise charges. If we take payment in future:</p>"
                    "<ul>"
                    "<li>You may request a refund by emailing "
                    f"{lc.SUPPORT_EMAIL} within 14 days of a charge you did not authorise, or where the paid "
                    "feature was unavailable because of a fault on our side.</li>"
                    "<li>Refunds, if granted, will be returned to the original payment method where the processor allows it.</li>"
                    "<li>App-store or platform fees billed by Apple, Google, or similar are subject to those stores’ refund rules.</li>"
                    "</ul>"
                ),
            },
            {
                "heading": "Donations and third parties",
                "body": (
                    "<p>If you donate or pay a third party (for example a volunteer platform), that is not a Sightra "
                    f"product charge. Contact that organisation, or {lc.SUPPORT_EMAIL} if you are unsure who billed you.</p>"
                ),
            },
        ],
        "footer": _footer(),
    }


def _third_party_services() -> dict:
    return {
        "slug": POLICY_SLUG_THIRD_PARTIES,
        "title": "Third-party services (SDK audit)",
        "sections": [
            {
                "heading": "How to read this audit",
                "body": (
                    "<p>This list is generated from the current Sightra codebase. It is an engineering inventory, "
                    "not a certification that each vendor’s processing is lawful in every jurisdiction. "
                    "No advertising or analytics SDKs are loaded unless you later opt in and we ship that code.</p>"
                ),
            },
            {
                "heading": "Authentication and accounts",
                "body": (
                    "<ul>"
                    "<li><strong>Supabase Auth</strong> — email/password and optional Google OAuth; stores account identifiers and sessions per your Supabase project region.</li>"
                    "<li><strong>Google OAuth</strong> — only if you tap Continue with Google; Google’s terms apply.</li>"
                    "</ul>"
                ),
            },
            {
                "heading": "AI and media",
                "body": (
                    "<ul>"
                    "<li><strong>Google Gemini</strong> — text generation from detection metadata and prompts (not raw camera frames in the current implementation).</li>"
                    "<li><strong>LiveKit</strong> — real-time audio/video when you use volunteer connect / live call.</li>"
                    "</ul>"
                ),
            },
            {
                "heading": "Maps",
                "body": (
                    "<ul>"
                    "<li><strong>OpenStreetMap tiles, Nominatim, OSRM</strong> — loaded in the browser on map pages; may receive search text or coordinates you submit.</li>"
                    "</ul>"
                ),
            },
            {
                "heading": "Interface delivery",
                "body": (
                    "<ul>"
                    "<li><strong>Tailwind CSS CDN</strong> — stylesheet runtime for layout.</li>"
                    "<li><strong>Google Fonts</strong> — Inter and Lexend.</li>"
                    "<li><strong>Google Material Symbols</strong> — icon font.</li>"
                    "</ul>"
                    "<p>These CDNs receive the network request needed to download assets (typically IP address and user agent).</p>"
                ),
            },
            {
                "heading": "Hosting",
                "body": (
                    "<p>The Django application is hosted by the operator’s hosting provider (for example a cPanel server). "
                    "Server logs may include IP addresses and error traces.</p>"
                ),
            },
            {
                "heading": "SDKs we do not ship today",
                "body": (
                    "<p>We do not currently include Google Analytics, Meta Pixel, Hotjar, advertising SDKs, or crash reporters "
                    "that phone home beyond the services above. If that changes, this page and the Cookie Policy will be updated "
                    "before those scripts load, and they will remain off until you accept optional cookies.</p>"
                ),
            },
        ],
        "footer": _footer(),
    }


def _licenses() -> dict:
    return {
        "slug": POLICY_SLUG_LICENSES,
        "title": "Licenses for fonts, icons, and images",
        "sections": [
            {
                "heading": "Fonts",
                "body": (
                    "<ul>"
                    '<li><strong>Inter</strong> — SIL Open Font License 1.1, served via Google Fonts. '
                    '<a href="https://github.com/rsms/inter" rel="noopener">Source and license</a>.</li>'
                    '<li><strong>Lexend</strong> — SIL Open Font License 1.1, served via Google Fonts. '
                    '<a href="https://fonts.google.com/specimen/Lexend" rel="noopener">Google Fonts listing</a>.</li>'
                    "</ul>"
                    "<p>SIL OFL fonts may be used in this product; they are not sold separately.</p>"
                ),
            },
            {
                "heading": "Icons",
                "body": (
                    "<ul>"
                    '<li><strong>Material Symbols Outlined</strong> — Apache License 2.0, Google. '
                    '<a href="https://fonts.google.com/icons" rel="noopener">Google Fonts Icons</a>.</li>'
                    "</ul>"
                ),
            },
            {
                "heading": "Product and brand images",
                "body": (
                    "<ul>"
                    "<li><strong>Sightra logo</strong> — copyright of the operator; used as the product mark.</li>"
                    "<li><strong>App icons</strong> — derived from the Sightra logo for the PWA.</li>"
                    "<li><strong>Landing photographs</strong> (landing-assistive.jpg, landing-mobility.png) — used by "
                    f"{lc.OPERATOR_NAME} for the Sightra marketing homepage. Contact {lc.CONTACT_EMAIL} for attribution "
                    "or take-down requests.</li>"
                    "</ul>"
                ),
            },
            {
                "heading": "Third-party photographs on feature pages",
                "body": (
                    "<p>Some feature pages historically hotlinked illustrative photos. Those should only be used with "
                    "a license. If you are a rights holder, email "
                    f"{lc.CONTACT_EMAIL} and we will remove the asset.</p>"
                ),
            },
            {
                "heading": "Open-source software",
                "body": (
                    "<p>Sightra is built with Django and other open-source packages listed in the project "
                    "requirements file. Their licenses remain with those projects.</p>"
                ),
            },
        ],
        "footer": _footer(),
    }
