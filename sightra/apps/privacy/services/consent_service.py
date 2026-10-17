from __future__ import annotations

from django.utils import timezone

from apps.privacy.constants import (
    CONSENT_CAMERA_FEATURE,
    CONSENT_CORE_SERVICE,
    CONSENT_LOCATION_FEATURE,
    CONSENT_MICROPHONE_FEATURE,
    CONSENT_OPTIONAL_HISTORY,
    CONSENT_PRIVACY_NOTICE,
    CONSENT_RESEARCH_FEEDBACK,
    CONSENT_AI_TRAINING,
    CONSENT_ANALYTICS,
    DECISION_DENIED,
    DECISION_GRANTED,
    DECISION_WITHDRAWN,
    POLICY_VERSION,
)
from apps.privacy.models import ConsentRecord, PrivacyProfile

SESSION_PRIVACY_KEY = "sightra_privacy_state"


def _session_state(request) -> dict:
    if not hasattr(request, "session"):
        return {}
    return request.session.get(SESSION_PRIVACY_KEY) or {}


def _save_session_state(request, state: dict) -> None:
    request.session[SESSION_PRIVACY_KEY] = state
    request.session.modified = True


def _user_id(request) -> str | None:
    user = getattr(request, "sightra_user", None)
    if user and user.get("id"):
        return str(user["id"])
    return None


def _truncate_agent(request) -> str:
    ua = (request.META.get("HTTP_USER_AGENT") or "")[:512]
    return ua


def record_consent(
    request,
    *,
    category: str,
    decision: str,
    policy_slug: str = "",
    purpose: str = "",
    metadata: dict | None = None,
) -> ConsentRecord:
    uid = _user_id(request)
    session_key = ""
    if request.session.session_key:
        session_key = request.session.session_key[:64]

    record = ConsentRecord.objects.create(
        supabase_user_id=uid or "",
        session_key=session_key,
        category=category,
        purpose=purpose,
        decision=decision,
        policy_slug=policy_slug,
        policy_version=POLICY_VERSION,
        user_agent=_truncate_agent(request),
        source="web",
        metadata=metadata or {},
    )

    state = _session_state(request)
    state[category] = {
        "decision": decision,
        "policy_version": POLICY_VERSION,
        "at": timezone.now().isoformat(),
    }
    _save_session_state(request, state)

    if uid:
        profile, _ = PrivacyProfile.objects.get_or_create(
            supabase_user_id=uid,
            defaults={"email": (getattr(request, "sightra_user", None) or {}).get("email") or ""},
        )
        now = timezone.now()
        if category == CONSENT_PRIVACY_NOTICE and decision == DECISION_GRANTED:
            profile.privacy_notice_version = POLICY_VERSION
            profile.privacy_notice_ack_at = now
        elif category == CONSENT_CORE_SERVICE and decision == DECISION_GRANTED:
            profile.core_service_accepted_at = now
        elif category == CONSENT_CAMERA_FEATURE and decision == DECISION_GRANTED:
            profile.camera_feature_consent_at = now
        elif category == CONSENT_MICROPHONE_FEATURE and decision == DECISION_GRANTED:
            profile.microphone_feature_consent_at = now
        elif category == CONSENT_LOCATION_FEATURE and decision == DECISION_GRANTED:
            profile.location_feature_consent_at = now
        elif category == CONSENT_OPTIONAL_HISTORY:
            profile.optional_interaction_history = decision == DECISION_GRANTED
        elif category == CONSENT_RESEARCH_FEEDBACK:
            profile.research_product_improvement = decision == DECISION_GRANTED
        elif category == CONSENT_AI_TRAINING:
            profile.ai_model_secondary_use = decision == DECISION_GRANTED
        elif category == CONSENT_ANALYTICS:
            profile.optional_analytics = decision == DECISION_GRANTED
        if decision == DECISION_WITHDRAWN:
            if category == CONSENT_OPTIONAL_HISTORY:
                profile.optional_interaction_history = False
            elif category == CONSENT_RESEARCH_FEEDBACK:
                profile.research_product_improvement = False
            elif category == CONSENT_AI_TRAINING:
                profile.ai_model_secondary_use = False
            elif category == CONSENT_ANALYTICS:
                profile.optional_analytics = False
        profile.save()

    return record


def _decision_for(request, category: str) -> str | None:
    uid = _user_id(request)
    if uid:
        try:
            profile = PrivacyProfile.objects.get(supabase_user_id=uid)
        except PrivacyProfile.DoesNotExist:
            profile = None
        if profile:
            if category == CONSENT_PRIVACY_NOTICE and profile.privacy_notice_ack_at:
                if profile.privacy_notice_version == POLICY_VERSION:
                    return DECISION_GRANTED
            if category == CONSENT_CORE_SERVICE and profile.core_service_accepted_at:
                return DECISION_GRANTED
            if category == CONSENT_CAMERA_FEATURE and profile.camera_feature_consent_at:
                return DECISION_GRANTED
            if category == CONSENT_MICROPHONE_FEATURE and profile.microphone_feature_consent_at:
                return DECISION_GRANTED
            if category == CONSENT_LOCATION_FEATURE and profile.location_feature_consent_at:
                return DECISION_GRANTED
            if category == CONSENT_OPTIONAL_HISTORY:
                return DECISION_GRANTED if profile.optional_interaction_history else DECISION_DENIED
            if category == CONSENT_RESEARCH_FEEDBACK:
                return DECISION_GRANTED if profile.research_product_improvement else DECISION_DENIED
            if category == CONSENT_AI_TRAINING:
                return DECISION_GRANTED if profile.ai_model_secondary_use else DECISION_DENIED
            if category == CONSENT_ANALYTICS:
                return DECISION_GRANTED if profile.optional_analytics else DECISION_DENIED

    state = _session_state(request).get(category)
    if state and state.get("policy_version") == POLICY_VERSION:
        return state.get("decision")
    return None


def has_privacy_notice_ack(request) -> bool:
    return _decision_for(request, CONSENT_PRIVACY_NOTICE) == DECISION_GRANTED


def has_core_service_consent(request) -> bool:
    return _decision_for(request, CONSENT_CORE_SERVICE) == DECISION_GRANTED


def has_camera_consent(request) -> bool:
    return (
        has_core_service_consent(request)
        and _decision_for(request, CONSENT_CAMERA_FEATURE) == DECISION_GRANTED
    )


def has_location_consent(request) -> bool:
    return (
        has_core_service_consent(request)
        and _decision_for(request, CONSENT_LOCATION_FEATURE) == DECISION_GRANTED
    )


def has_microphone_consent(request) -> bool:
    return (
        has_core_service_consent(request)
        and _decision_for(request, CONSENT_MICROPHONE_FEATURE) == DECISION_GRANTED
    )


def consent_status_payload(request) -> dict:
    categories = [
        CONSENT_PRIVACY_NOTICE,
        CONSENT_CORE_SERVICE,
        CONSENT_CAMERA_FEATURE,
        CONSENT_MICROPHONE_FEATURE,
        CONSENT_LOCATION_FEATURE,
        CONSENT_OPTIONAL_HISTORY,
        CONSENT_RESEARCH_FEEDBACK,
        CONSENT_AI_TRAINING,
        CONSENT_ANALYTICS,
    ]
    decisions = {c: _decision_for(request, c) for c in categories}
    return {
        "policy_version": POLICY_VERSION,
        "authenticated": bool(_user_id(request)),
        "decisions": decisions,
        "requires_onboarding": not (
            decisions.get(CONSENT_PRIVACY_NOTICE) == DECISION_GRANTED
            and decisions.get(CONSENT_CORE_SERVICE) == DECISION_GRANTED
        ),
    }


def delete_user_privacy_data(supabase_user_id: str) -> int:
    deleted, _ = ConsentRecord.objects.filter(supabase_user_id=supabase_user_id).delete()
    PrivacyProfile.objects.filter(supabase_user_id=supabase_user_id).delete()
    return deleted
