from django.contrib import admin

from .models import UserPreference


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ("email", "supabase_user_id", "theme", "updated_at")
    search_fields = ("email", "supabase_user_id")
