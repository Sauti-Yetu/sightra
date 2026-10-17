from django.contrib import admin

from .models import ConsentRecord, PrivacyProfile


@admin.register(PrivacyProfile)
class PrivacyProfileAdmin(admin.ModelAdmin):
    list_display = ("email", "supabase_user_id", "privacy_notice_version", "updated_at")
    search_fields = ("email", "supabase_user_id")


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ("category", "decision", "supabase_user_id", "policy_version", "created_at")
    list_filter = ("category", "decision")
    search_fields = ("supabase_user_id", "session_key")
