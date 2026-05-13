"""
tracking/views.py — Email open and click tracking endpoints.

Open tracking:  GET /tracking/open/<tracking_id>/
  → Returns a 1×1 transparent GIF, marks email as opened.

Click tracking: GET /tracking/click/<tracking_id>/?url=<encoded_url>
  → Marks email as clicked, redirects to original URL.
"""
import base64
import logging
import urllib.parse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.cache import never_cache
from django.utils.timezone import now
from campaigns.models import EmailLog

logger = logging.getLogger(__name__)

# 1×1 transparent GIF (43 bytes)
TRACKING_PIXEL = base64.b64decode(
    'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
)


@never_cache
def track_open(request, tracking_id):
    """Record email open event, return invisible tracking pixel."""
    try:
        log = EmailLog.objects.get(tracking_id=tracking_id)
        if not log.opened:
            log.opened = True
            log.opened_at = now()
            log.save(update_fields=['opened', 'opened_at'])
            logger.info(f"Email opened: {log.recipient_email} (campaign: {log.campaign.campaign_name})")
    except EmailLog.DoesNotExist:
        logger.warning(f"Track open: invalid tracking_id {tracking_id}")
    except Exception as e:
        logger.error(f"Track open error: {e}")

    response = HttpResponse(TRACKING_PIXEL, content_type='image/gif')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@never_cache
def track_click(request, tracking_id):
    """Record email click event, redirect to original URL."""
    redirect_url = request.GET.get('url', '')

    try:
        decoded_url = urllib.parse.unquote(redirect_url)
    except Exception:
        decoded_url = '/'

    try:
        log = EmailLog.objects.get(tracking_id=tracking_id)
        if not log.clicked:
            log.clicked = True
            log.clicked_at = now()
            log.save(update_fields=['clicked', 'clicked_at'])
            logger.info(f"Email clicked: {log.recipient_email} → {decoded_url}")
    except EmailLog.DoesNotExist:
        logger.warning(f"Track click: invalid tracking_id {tracking_id}")
    except Exception as e:
        logger.error(f"Track click error: {e}")

    if decoded_url and decoded_url.startswith(('http://', 'https://')):
        return HttpResponseRedirect(decoded_url)
    return HttpResponseRedirect('/')
