"""Versioned consent categories and policy identifiers."""

POLICY_VERSION = "2026.10.1"
POLICY_EFFECTIVE_DATE = "2026-10-17"

# Slugs for legal documents (see content/policies.py)
POLICY_SLUG_PRIVACY = "privacy-policy"
POLICY_SLUG_TERMS = "terms-of-use"
POLICY_SLUG_AI = "ai-transparency"
POLICY_SLUG_COOKIES = "cookie-storage"

CONSENT_PRIVACY_NOTICE = "privacy_notice_ack"
CONSENT_CORE_SERVICE = "core_service_processing"
CONSENT_CAMERA_FEATURE = "camera_environmental_analysis"
CONSENT_MICROPHONE_FEATURE = "microphone_voice_input"
CONSENT_LOCATION_FEATURE = "location_navigation"
CONSENT_OPTIONAL_HISTORY = "optional_interaction_history"
CONSENT_RESEARCH_FEEDBACK = "research_product_improvement"
CONSENT_AI_TRAINING = "ai_model_secondary_use"
CONSENT_ANALYTICS = "optional_analytics"

DECISION_GRANTED = "granted"
DECISION_DENIED = "denied"
DECISION_WITHDRAWN = "withdrawn"

OPTIONAL_CONSENTS = frozenset(
    {
        CONSENT_OPTIONAL_HISTORY,
        CONSENT_RESEARCH_FEEDBACK,
        CONSENT_AI_TRAINING,
        CONSENT_ANALYTICS,
    }
)

FEATURE_CONSENTS = frozenset(
    {
        CONSENT_CAMERA_FEATURE,
        CONSENT_MICROPHONE_FEATURE,
        CONSENT_LOCATION_FEATURE,
    }
)
