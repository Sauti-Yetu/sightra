from django.db import models


class LocalUserProfile(models.Model):
    """Local cache of Supabase user for admin/reporting when offline from Supabase."""

    supabase_user_id = models.UUIDField(unique=True, db_index=True)
    email = models.EmailField(blank=True, default="")
    display_name = models.CharField(max_length=255, blank=True, default="")
    theme_preference = models.CharField(max_length=16, default="light")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "User profile (local)"
        verbose_name_plural = "User profiles (local)"

    def __str__(self) -> str:
        return self.email or str(self.supabase_user_id)


class LocalActivityEvent(models.Model):
    """Fallback activity log stored in Django DB."""

    supabase_user_id = models.UUIDField(db_index=True, null=True, blank=True)
    event_type = models.CharField(max_length=64, db_index=True)
    path = models.CharField(max_length=512, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Activity event (local)"
        verbose_name_plural = "Activity events (local)"
