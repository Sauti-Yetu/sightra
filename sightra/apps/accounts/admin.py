from django.contrib import admin

from .models import LocalActivityEvent, LocalUserProfile


@admin.register(LocalUserProfile)
class LocalUserProfileAdmin(admin.ModelAdmin):
    list_display = ("email", "display_name", "theme_preference", "last_seen_at", "updated_at")
    search_fields = ("email", "display_name", "supabase_user_id")
    readonly_fields = ("supabase_user_id", "created_at", "updated_at")


@admin.register(LocalActivityEvent)
class LocalActivityEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "path", "supabase_user_id", "created_at")
    list_filter = ("event_type",)
    search_fields = ("path", "supabase_user_id")
    readonly_fields = ("created_at",)
