from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from .models import Campaign, EmailLog
from CreateUser.models import emailUsers
from CreateUser.utils import profileCompletetion


def _get_user(request):
    """Helper: returns (user, redirect_response). If not logged in, redirect_response is set."""
    user_id = request.session.get('user_id')
    if not user_id:
        return None, redirect('Login')
    user = get_object_or_404(emailUsers, pk=user_id)
    return user, None


def campaign_list(request):
    user, redir = _get_user(request)
    if redir:
        messages.warning(request, "Login first")
        return redir

    campaigns = Campaign.objects.filter(user=user).order_by('-created_at')

    # Summary stats
    total_campaigns = campaigns.count()
    total_sent = sum(c.sent_count for c in campaigns)
    total_failed = sum(c.failed_count for c in campaigns)
    avg_success = round(
        (total_sent / (total_sent + total_failed) * 100) if (total_sent + total_failed) > 0 else 0, 1
    )

    return render(request, 'campaigns/campaign_list.html', {
        'title': 'Campaign History',
        'username': user.name.split(' ')[0],
        'image': user.image,
        'progress': profileCompletetion(user),
        'campaigns': campaigns,
        'total_campaigns': total_campaigns,
        'total_sent': total_sent,
        'total_failed': total_failed,
        'avg_success': avg_success,
    })


def campaign_detail(request, campaign_id):
    user, redir = _get_user(request)
    if redir:
        messages.warning(request, "Login first")
        return redir

    campaign = get_object_or_404(Campaign, pk=campaign_id, user=user)
    logs = EmailLog.objects.filter(campaign=campaign)

    sent_logs = logs.filter(status='sent')
    failed_logs = logs.filter(status='failed')
    opened_logs = logs.filter(opened=True)
    clicked_logs = logs.filter(clicked=True)

    open_rate = round((opened_logs.count() / sent_logs.count() * 100) if sent_logs.count() > 0 else 0, 1)
    click_rate = round((clicked_logs.count() / sent_logs.count() * 100) if sent_logs.count() > 0 else 0, 1)

    return render(request, 'campaigns/campaign_detail.html', {
        'title': f'Campaign: {campaign.campaign_name}',
        'user': user,
        'username': user.name.split(' ')[0],
        'image': user.image,
        'progress': profileCompletetion(user),
        'campaign': campaign,
        'c': {'body': campaign.email_body, 'subject': campaign.subject},
        'logs': logs,
        'sent_logs': sent_logs,
        'failed_logs': failed_logs,
        'open_rate': open_rate,
        'click_rate': click_rate,
        'opened_count': opened_logs.count(),
        'clicked_count': clicked_logs.count(),
    })


def campaign_progress(request, campaign_id):
    """JSON endpoint for live progress polling."""
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    campaign = get_object_or_404(Campaign, pk=campaign_id, user__id=user_id)
    percent = round((campaign.sent_count + campaign.failed_count) / campaign.total_emails * 100, 1) \
        if campaign.total_emails > 0 else 0

    return JsonResponse({
        'campaign_id': campaign.id,
        'status': campaign.status,
        'total': campaign.total_emails,
        'sent': campaign.sent_count,
        'failed': campaign.failed_count,
        'pending': campaign.pending_count,
        'percent': percent,
        'success_rate': campaign.success_rate,
    })


def campaign_logs(request, campaign_id):
    """JSON endpoint returning email logs for a campaign."""
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    campaign = get_object_or_404(Campaign, pk=campaign_id, user__id=user_id)
    status_filter = request.GET.get('status', '')
    logs = EmailLog.objects.filter(campaign=campaign)
    if status_filter:
        logs = logs.filter(status=status_filter)

    data = [
        {
            'id': log.id,
            'email': log.recipient_email,
            'name': log.recipient_name,
            'status': log.status,
            'error': log.error_message or '',
            'sent_at': log.sent_at.isoformat() if log.sent_at else None,
            'opened': log.opened,
            'clicked': log.clicked,
        }
        for log in logs
    ]
    return JsonResponse({'logs': data, 'count': len(data)})


def export_campaign_csv(request, campaign_id):
    """Generate and return a CSV export of campaign logs."""
    import csv
    from django.http import HttpResponse

    user_id = request.session.get('user_id')
    if not user_id:
        return HttpResponse("Unauthorized", status=401)

    campaign = get_object_or_404(Campaign, pk=campaign_id, user__id=user_id)
    logs = EmailLog.objects.filter(campaign=campaign).order_by('sent_at')

    # Create response object
    response = HttpResponse(content_type='text/csv')
    filename = f"report_{campaign.campaign_name.replace(' ', '_')}_{campaign.id}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    # Header row
    writer.writerow([
        'Recipient Name', 'Recipient Email', 'Status', 
        'Sent At', 'Opened', 'Opened At', 
        'Clicked', 'Clicked At', 'Error Message'
    ])

    for log in logs:
        writer.writerow([
            log.recipient_name,
            log.recipient_email,
            log.status.capitalize(),
            log.sent_at.strftime('%Y-%m-%d %H:%M:%S') if log.sent_at else 'N/A',
            'Yes' if log.opened else 'No',
            log.opened_at.strftime('%Y-%m-%d %H:%M:%S') if log.opened_at else 'N/A',
            'Yes' if log.clicked else 'No',
            log.clicked_at.strftime('%Y-%m-%d %H:%M:%S') if log.clicked_at else 'N/A',
            log.error_message or ''
        ])

    return response
