from __future__ import annotations

from apps.privacy.models import DataRequest


ALLOWED_KINDS = {
    DataRequest.KIND_DELETION,
    DataRequest.KIND_ACCESS,
    DataRequest.KIND_CORRECTION,
    DataRequest.KIND_PARENTAL,
    DataRequest.KIND_UNSUBSCRIBE,
}


def create_data_request(
    *,
    kind: str,
    email: str,
    details: str = "",
    guardian_email: str = "",
    supabase_user_id: str = "",
) -> DataRequest:
    if kind not in ALLOWED_KINDS:
        raise ValueError("Unknown request type")
    email_clean = (email or "").strip().lower()
    if not email_clean or "@" not in email_clean:
        raise ValueError("A valid email is required")
    return DataRequest.objects.create(
        kind=kind,
        email=email_clean[:254],
        guardian_email=(guardian_email or "").strip().lower()[:254],
        details=(details or "").strip()[:4000],
        supabase_user_id=(supabase_user_id or "")[:64],
    )
