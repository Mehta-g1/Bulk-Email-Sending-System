from django.contrib import admin
from .models import Campaign, EmailLog


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['campaign_name', 'user', 'status', 'total_emails', 'sent_count', 'failed_count', 'success_rate', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['campaign_name', 'user__name', 'user__email_address']
    readonly_fields = ['created_at', 'completed_at', 'success_rate']


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['recipient_email', 'recipient_name', 'status', 'opened', 'clicked', 'sent_at', 'campaign']
    list_filter = ['status', 'opened', 'clicked', 'sent_at']
    search_fields = ['recipient_email', 'recipient_name', 'campaign__campaign_name']
    readonly_fields = ['tracking_id', 'sent_at', 'opened_at', 'clicked_at']
