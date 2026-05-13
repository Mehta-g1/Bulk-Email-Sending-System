from django.urls import path
from . import views

urlpatterns = [
    # Email endpoints
    path('send-email/', views.api_send_email, name='api_send_email'),
    path('send-bulk/', views.api_send_bulk, name='api_send_bulk'),

    # OTP endpoints (no auth needed)
    path('send-otp/', views.api_send_otp, name='api_send_otp'),
    path('verify-otp/', views.api_verify_otp, name='api_verify_otp'),

    # Data endpoints
    path('campaigns/', views.api_campaigns, name='api_campaigns'),
    path('campaign/<int:campaign_id>/progress/', views.api_campaign_progress, name='api_campaign_progress'),
    path('logs/', views.api_logs, name='api_logs'),
    path('stats/', views.api_stats, name='api_stats'),

    # Key management
    path('generate-key/', views.api_generate_key, name='api_generate_key'),
]
