from django.contrib import admin
from .models import OTPVerification


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ['email', 'purpose', 'is_verified', 'attempts', 'created_at', 'expiry_time']
    list_filter = ['is_verified', 'purpose', 'created_at']
    search_fields = ['email']
    readonly_fields = ['created_at', 'expiry_time', 'otp']
