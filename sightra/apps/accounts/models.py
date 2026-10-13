from django.db import models


class UserPreference(models.Model):
    """Optional local cache of UI preferences (theme, accessibility)."""

    supabase_user_id = models.CharField(max_length=64, unique=True)
    email = models.EmailField(blank=True)
    theme = models.CharField(max_length=16, default="light")
    accessibility_json = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.email or self.supabase_user_id
