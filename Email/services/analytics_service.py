"""
analytics_service.py — Aggregated analytics for dashboard.
"""
from django.db.models import Count, Sum, Avg, Q
from django.utils.timezone import now
from datetime import timedelta

from campaigns.models import Campaign, EmailLog
from CreateUser.models import emailUsers


def get_user_stats(user: emailUsers) -> dict:
    """Return all key analytics for a user."""
    campaigns = Campaign.objects.filter(user=user)

    total_campaigns = campaigns.count()
    total_sent = campaigns.aggregate(s=Sum('sent_count'))['s'] or 0
    total_failed = campaigns.aggregate(s=Sum('failed_count'))['s'] or 0
    total_emails = campaigns.aggregate(s=Sum('total_emails'))['s'] or 0

    success_rate = round(total_sent / total_emails * 100, 1) if total_emails > 0 else 0

    # Open & click rates
    logs = EmailLog.objects.filter(campaign__user=user)
    sent_logs = logs.filter(status='sent')
    opened = sent_logs.filter(opened=True).count()
    clicked = sent_logs.filter(clicked=True).count()
    sent_count = sent_logs.count()

    open_rate = round(opened / sent_count * 100, 1) if sent_count > 0 else 0
    click_rate = round(clicked / sent_count * 100, 1) if sent_count > 0 else 0

    # Emails per day (last 7 days)
    daily_data = []
    for i in range(6, -1, -1):
        day = now().date() - timedelta(days=i)
        count = logs.filter(
            sent_at__date=day,
            status='sent'
        ).count()
        daily_data.append({'date': day.strftime('%b %d'), 'count': count})

    # Top campaigns by sent_count
    top_campaigns = campaigns.order_by('-sent_count')[:5].values(
        'campaign_name', 'sent_count', 'failed_count', 'success_rate', 'created_at'
    )

    # Recent email logs
    recent_logs = logs.order_by('-sent_at')[:20].values(
        'recipient_email', 'recipient_name', 'status',
        'sent_at', 'opened', 'clicked', 'campaign__campaign_name'
    )

    # Running campaigns
    running = campaigns.filter(status='running').first()

    return {
        'total_campaigns': total_campaigns,
        'total_sent': total_sent,
        'total_failed': total_failed,
        'total_emails': total_emails,
        'success_rate': success_rate,
        'open_rate': open_rate,
        'click_rate': click_rate,
        'opened_count': opened,
        'clicked_count': clicked,
        'daily_data': list(daily_data),
        'top_campaigns': list(top_campaigns),
        'recent_logs': list(recent_logs),
        'running_campaign': running,
    }


def get_platform_stats() -> dict:
    """Admin-level platform-wide stats."""
    total_users = emailUsers.objects.count()
    total_campaigns = Campaign.objects.count()
    total_sent = Campaign.objects.aggregate(s=Sum('sent_count'))['s'] or 0
    total_failed = Campaign.objects.aggregate(s=Sum('failed_count'))['s'] or 0

    # Active users (sent at least 1 email)
    active_users = Campaign.objects.filter(sent_count__gt=0).values('user').distinct().count()

    return {
        'total_users': total_users,
        'active_users': active_users,
        'total_campaigns': total_campaigns,
        'total_sent': total_sent,
        'total_failed': total_failed,
    }
