"""Versioned consent categories and policy identifiers."""

POLICY_VERSION = "2026.10.2"
POLICY_EFFECTIVE_DATE = "2026-10-29"

# Slugs for legal documents (see content/policies.py)
POLICY_SLUG_PRIVACY = "privacy-policy"
POLICY_SLUG_TERMS = "terms-of-service"
POLICY_SLUG_TERMS_ALIAS = "terms-of-use"
POLICY_SLUG_AI = "ai-transparency"
POLICY_SLUG_COOKIES = "cookie-policy"
POLICY_SLUG_COOKIES_ALIAS = "cookie-storage"
POLICY_SLUG_REFUND = "refund-policy"
POLICY_SLUG_LICENSES = "licenses"
POLICY_SLUG_THIRD_PARTIES = "third-party-services"

POLICY_ALIASES = {
    POLICY_SLUG_TERMS_ALIAS: POLICY_SLUG_TERMS,
    POLICY_SLUG_COOKIES_ALIAS: POLICY_SLUG_COOKIES,
}

CONSENT_PRIVACY_NOTICE = "privacy_notice_ack"
CONSENT_CORE_SERVICE = "core_service_processing"
CONSENT_CAMERA_FEATURE = "camera_environmental_analysis"
CONSENT_MICROPHONE_FEATURE = "microphone_voice_input"
CONSENT_LOCATION_FEATURE = "location_navigation"
CONSENT_OPTIONAL_HISTORY = "optional_interaction_history"
CONSENT_RESEARCH_FEEDBACK = "research_product_improvement"
CONSENT_AI_TRAINING = "ai_model_secondary_use"
CONSENT_ANALYTICS = "optional_analytics"
CONSENT_COOKIES_OPTIONAL = "optional_cookies"
CONSENT_MARKETING_EMAIL = "marketing_email"
CONSENT_PARENTAL = "parental_consent"
CONSENT_AGE_ADULT = "age_attestation_adult"

DECISION_GRANTED = "granted"
DECISION_DENIED = "denied"
DECISION_WITHDRAWN = "withdrawn"

OPTIONAL_CONSENTS = frozenset(
    {
        CONSENT_OPTIONAL_HISTORY,
        CONSENT_RESEARCH_FEEDBACK,
        CONSENT_AI_TRAINING,
        CONSENT_ANALYTICS,
        CONSENT_COOKIES_OPTIONAL,
        CONSENT_MARKETING_EMAIL,
    }
)

FEATURE_CONSENTS = frozenset(
    {
        CONSENT_CAMERA_FEATURE,
        CONSENT_MICROPHONE_FEATURE,
        CONSENT_LOCATION_FEATURE,
    }
)
