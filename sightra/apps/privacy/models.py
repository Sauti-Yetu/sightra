from django.db import models

from .constants import POLICY_VERSION


class PrivacyProfile(models.Model):
    """Current privacy choices for a signed-in user (fast lookup)."""

    supabase_user_id = models.CharField(max_length=64, unique=True)
    email = models.EmailField(blank=True)
    privacy_notice_version = models.CharField(max_length=32, blank=True)
    privacy_notice_ack_at = models.DateTimeField(null=True, blank=True)
    core_service_accepted_at = models.DateTimeField(null=True, blank=True)
    optional_interaction_history = models.BooleanField(default=False)
    research_product_improvement = models.BooleanField(default=False)
    ai_model_secondary_use = models.BooleanField(default=False)
    optional_analytics = models.BooleanField(default=False)
    optional_cookies = models.BooleanField(default=False)
    marketing_emails_opt_in = models.BooleanField(default=False)
    age_confirmed_adult = models.BooleanField(default=False)
    parental_consent_at = models.DateTimeField(null=True, blank=True)
    guardian_email = models.EmailField(blank=True)
    camera_feature_consent_at = models.DateTimeField(null=True, blank=True)
    microphone_feature_consent_at = models.DateTimeField(null=True, blank=True)
    location_feature_consent_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.email or self.supabase_user_id


class ConsentRecord(models.Model):
    """Append-only audit log of consent decisions."""

    supabase_user_id = models.CharField(max_length=64, blank=True, db_index=True)
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    category = models.CharField(max_length=64, db_index=True)
    purpose = models.CharField(max_length=255, blank=True)
    decision = models.CharField(max_length=16)
    policy_slug = models.CharField(max_length=64, blank=True)
    policy_version = models.CharField(max_length=32, default=POLICY_VERSION)
    user_agent = models.CharField(max_length=512, blank=True)
    source = models.CharField(max_length=32, default="web")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.category}:{self.decision}@{self.created_at.isoformat()}"


class DataRequest(models.Model):
    """Access, deletion, parental-consent, and unsubscribe requests (including guests)."""

    KIND_DELETION = "deletion"
    KIND_ACCESS = "access"
    KIND_CORRECTION = "correction"
    KIND_PARENTAL = "parental_consent"
    KIND_UNSUBSCRIBE = "unsubscribe"
    KIND_CHOICES = (
        (KIND_DELETION, "Delete my data"),
        (KIND_ACCESS, "Download / access my data"),
        (KIND_CORRECTION, "Correct my data"),
        (KIND_PARENTAL, "Parental consent"),
        (KIND_UNSUBSCRIBE, "Unsubscribe from emails"),
    )
    STATUS_OPEN = "open"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = (
        (STATUS_OPEN, "Open"),
        (STATUS_COMPLETED, "Completed"),
    )

    kind = models.CharField(max_length=32, choices=KIND_CHOICES, db_index=True)
    email = models.EmailField()
    guardian_email = models.EmailField(blank=True)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_OPEN, db_index=True)
    supabase_user_id = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.kind}:{self.email}:{self.status}"


class EmailPreference(models.Model):
    """Marketing/product email opt-in. Default is unsubscribed / not opted in."""

    email = models.EmailField(unique=True)
    marketing_opt_in = models.BooleanField(default=False)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.email
