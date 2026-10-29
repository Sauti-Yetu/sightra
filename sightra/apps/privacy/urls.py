from django.urls import path

from . import views

urlpatterns = [
    path("status/", views.api_consent_status, name="privacy-status"),
    path("consent/", views.api_consent_update, name="privacy-consent"),
    path("onboarding/", views.api_onboarding_complete, name="privacy-onboarding"),
    path("cookies/", views.api_cookie_choice, name="privacy-cookies"),
    path("export/", views.api_data_export, name="privacy-export"),
    path("delete-account-data/", views.api_delete_account_data, name="privacy-delete"),
]
