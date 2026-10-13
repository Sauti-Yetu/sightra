from django.urls import path

from . import views

urlpatterns = [
    path("auth/me/", views.auth_me, name="auth-me"),
    path("auth/signin/", views.auth_signin_api, name="auth-signin-api"),
    path("auth/signup/", views.auth_signup_api, name="auth-signup-api"),
    path("auth/signout/", views.auth_signout_api, name="auth-signout-api"),
    path("preferences/", views.preferences_api, name="auth-preferences"),
]
