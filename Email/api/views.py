"""
api/views.py — REST API endpoints for the Email Automation Platform.

Endpoints:
  POST /api/send-email/     → send single email
  POST /api/send-bulk/      → create campaign + multithreaded bulk send
  POST /api/send-otp/       → send OTP to an email
  POST /api/verify-otp/     → verify OTP
  GET  /api/campaigns/      → list user campaigns
  GET  /api/logs/           → email logs (filter by campaign_id)
  GET  /api/stats/          → analytics stats
  POST /api/generate-key/   → generate/regenerate API key
  GET  /api/campaign/<id>/progress/ → live progress JSON

Auth: Authorization: Bearer <API_KEY>
"""
import json
import secrets
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.core.mail import EmailMessage, get_connection
from django.utils.timezone import now

from .auth import api_key_required
from CreateUser.models import emailUsers, Receipent
from EmailTemplates.models import Template
from campaigns.models import Campaign, EmailLog
from otp.services import send_otp, verify_otp
from services.analytics_service import get_user_stats
from services.email_service import send_bulk_email_campaign

logger = logging.getLogger(__name__)


def _json_body(request) -> dict:
    """Parse JSON body safely."""
    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return {}


def _error(message, status=400) -> JsonResponse:
    return JsonResponse({'success': False, 'error': message}, status=status)


def _ok(data: dict, status=200) -> JsonResponse:
    return JsonResponse({'success': True, **data}, status=status)


# ────────────────────────────────────────────
# POST /api/send-email/
# ────────────────────────────────────────────
@csrf_exempt
@require_POST
@api_key_required
def api_send_email(request):
    """
    Send a single email.
    Body: {to_email, subject, body, [from_name]}
    """
    data = _json_body(request)
    to_email = data.get('to_email', '').strip()
    subject = data.get('subject', '').strip()
    body = data.get('body', '').strip()

    if not all([to_email, subject, body]):
        return _error('to_email, subject, and body are required.')

    user = request.api_user
    if not user.email_password:
        return _error('SMTP not configured. Update your account settings.', 422)

    try:
        from services.email_service import _get_smtp_connection
        conn = _get_smtp_connection(user)
        msg = EmailMessage(
            subject=subject, body=body,
            from_email=user.email_address,
            to=[to_email], connection=conn
        )
        msg.content_subtype = 'html'
        msg.send()
        return _ok({'message': f'Email sent to {to_email}'})
    except Exception as e:
        logger.error(f"API send-email error: {e}")
        return _error(f'Failed to send email: {str(e)}', 500)


# ────────────────────────────────────────────
# POST /api/send-bulk/
# ────────────────────────────────────────────
@csrf_exempt
@require_POST
@api_key_required
def api_send_bulk(request):
    """
    Start a bulk email campaign.
    Body: {recipient_ids: [1,2,3], campaign_name: "...", [group_id: int]}
    """
    data = _json_body(request)
    user = request.api_user

    recipient_ids = data.get('recipient_ids', [])
    group_id = data.get('group_id')
    campaign_name = data.get('campaign_name', '').strip()

    # Allow selecting by group
    if group_id and not recipient_ids:
        recipient_ids = list(
            Receipent.objects.filter(Sender=user, group__id=group_id).values_list('id', flat=True)
        )

    if not recipient_ids:
        return _error('Provide recipient_ids or group_id.')

    if not user.email_password:
        return _error('SMTP not configured.', 422)

    try:
        campaign = send_bulk_email_campaign(
            user_id=user.id,
            selected_ids=recipient_ids,
            campaign_name=campaign_name or None,
            base_url=request.build_absolute_uri('/').rstrip('/'),
        )
        return _ok({
            'campaign_id': campaign.id,
            'campaign_name': campaign.campaign_name,
            'total': campaign.total_emails,
            'sent': campaign.sent_count,
            'failed': campaign.failed_count,
            'success_rate': campaign.success_rate,
            'status': campaign.status,
        })
    except ValueError as e:
        return _error(str(e), 422)
    except Exception as e:
        logger.error(f"API send-bulk error: {e}")
        return _error(f'Bulk send failed: {str(e)}', 500)


# ────────────────────────────────────────────
# POST /api/send-otp/
# ────────────────────────────────────────────
@csrf_exempt
@require_POST
def api_send_otp(request):
    """
    Send OTP. Does NOT require API key — open endpoint.
    Body: {email, purpose}
    """
    data = _json_body(request)
    email = data.get('email', '').strip()
    purpose = data.get('purpose', 'general')

    if not email:
        return _error('email is required.')

    result = send_otp(email, purpose)
    if result['success']:
        return _ok({'message': result['message']})
    return _error(result['message'], 500)


# ────────────────────────────────────────────
# POST /api/verify-otp/
# ────────────────────────────────────────────
@csrf_exempt
@require_POST
def api_verify_otp(request):
    """
    Verify OTP. Does NOT require API key.
    Body: {email, otp, purpose}
    """
    data = _json_body(request)
    email = data.get('email', '').strip()
    otp_code = data.get('otp', '').strip()
    purpose = data.get('purpose', 'general')

    if not email or not otp_code:
        return _error('email and otp are required.')

    result = verify_otp(email, otp_code, purpose)
    if result['success']:
        return _ok({'message': result['message']})
    return _error(result['message'], 400)


# ────────────────────────────────────────────
# GET /api/campaigns/
# ────────────────────────────────────────────
@require_GET
@api_key_required
def api_campaigns(request):
    """List all campaigns for the authenticated user."""
    user = request.api_user
    status_filter = request.GET.get('status', '')
    campaigns = Campaign.objects.filter(user=user)
    if status_filter:
        campaigns = campaigns.filter(status=status_filter)

    data = [
        {
            'id': c.id,
            'name': c.campaign_name,
            'status': c.status,
            'total': c.total_emails,
            'sent': c.sent_count,
            'failed': c.failed_count,
            'success_rate': c.success_rate,
            'created_at': c.created_at.isoformat(),
            'completed_at': c.completed_at.isoformat() if c.completed_at else None,
        }
        for c in campaigns
    ]
    return _ok({'campaigns': data, 'count': len(data)})


# ────────────────────────────────────────────
# GET /api/logs/
# ────────────────────────────────────────────
@require_GET
@api_key_required
def api_logs(request):
    """
    Get email logs.
    Query params: campaign_id, status, limit (default 50)
    """
    user = request.api_user
    campaign_id = request.GET.get('campaign_id')
    status_filter = request.GET.get('status', '')
    limit = min(int(request.GET.get('limit', 50)), 200)

    logs = EmailLog.objects.filter(campaign__user=user)
    if campaign_id:
        logs = logs.filter(campaign__id=campaign_id)
    if status_filter:
        logs = logs.filter(status=status_filter)

    logs = logs[:limit]
    data = [
        {
            'id': log.id,
            'campaign': log.campaign.campaign_name,
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
    return _ok({'logs': data, 'count': len(data)})


# ────────────────────────────────────────────
# GET /api/stats/
# ────────────────────────────────────────────
@require_GET
@api_key_required
def api_stats(request):
    """Return analytics stats for the authenticated user."""
    user = request.api_user
    stats = get_user_stats(user)
    return _ok(stats)


# ────────────────────────────────────────────
# GET /api/campaign/<id>/progress/
# ────────────────────────────────────────────
@require_GET
@api_key_required
def api_campaign_progress(request, campaign_id):
    """Live progress of a specific campaign."""
    user = request.api_user
    try:
        campaign = Campaign.objects.get(pk=campaign_id, user=user)
    except Campaign.DoesNotExist:
        return _error('Campaign not found.', 404)

    percent = round(
        (campaign.sent_count + campaign.failed_count) / campaign.total_emails * 100, 1
    ) if campaign.total_emails > 0 else 0

    return _ok({
        'campaign_id': campaign.id,
        'status': campaign.status,
        'total': campaign.total_emails,
        'sent': campaign.sent_count,
        'failed': campaign.failed_count,
        'pending': campaign.pending_count,
        'percent': percent,
        'success_rate': campaign.success_rate,
    })


# ────────────────────────────────────────────
# POST /api/generate-key/
# ────────────────────────────────────────────
@csrf_exempt
@require_POST
def api_generate_key(request):
    """
    Generate or regenerate API key for the logged-in session user.
    Does NOT use API key auth (uses session auth instead).
    """
    user_id = request.session.get('user_id')
    if not user_id:
        return _error('Session login required to generate API key.', 401)

    try:
        user = emailUsers.objects.get(pk=user_id)
    except emailUsers.DoesNotExist:
        return _error('User not found.', 404)

    # Generate secure 48-char hex key
    new_key = secrets.token_hex(24)
    user.api_key = new_key
    user.api_key_created_at = now()
    user.api_usage_count = 0
    user.save(update_fields=['api_key', 'api_key_created_at', 'api_usage_count'])

    from django.shortcuts import redirect
    from django.contrib import messages
    messages.success(request, 'API key generated. Store it securely — it will not be shown again.')
    return redirect('account_settings')
