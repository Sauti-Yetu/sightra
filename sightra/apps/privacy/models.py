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
