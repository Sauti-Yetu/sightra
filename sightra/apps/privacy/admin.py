from django.contrib import admin

from .models import ConsentRecord, DataRequest, EmailPreference, PrivacyProfile


@admin.register(PrivacyProfile)
class PrivacyProfileAdmin(admin.ModelAdmin):
    list_display = ("email", "supabase_user_id", "privacy_notice_version", "updated_at")
    search_fields = ("email", "supabase_user_id")


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ("category", "decision", "supabase_user_id", "policy_version", "created_at")
    list_filter = ("category", "decision")
    search_fields = ("supabase_user_id", "session_key")


@admin.register(DataRequest)
class DataRequestAdmin(admin.ModelAdmin):
    list_display = ("kind", "email", "status", "created_at")
    list_filter = ("kind", "status")
    search_fields = ("email", "guardian_email", "details")


@admin.register(EmailPreference)
class EmailPreferenceAdmin(admin.ModelAdmin):
    list_display = ("email", "marketing_opt_in", "unsubscribed_at", "updated_at")
    search_fields = ("email",)
