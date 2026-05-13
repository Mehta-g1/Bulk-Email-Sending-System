"""
email_service.py — Multithreaded bulk email sending with Campaign tracking.

Architecture:
  - Each bulk send creates a Campaign record
  - Each email attempt creates an EmailLog record
  - ThreadPoolExecutor(max_workers=5) sends emails in parallel
  - Thread-safe updates to campaign progress via threading.Lock
  - Automatic retry (up to 2 retries) on transient SMTP errors
  - Personalised placeholder replacement: {{name}}, {{email}}, {{company}}
"""
import threading
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.core.mail import EmailMessage, get_connection
from django.utils.timezone import now
from django.db import transaction

from CreateUser.models import emailUsers, Receipent
from EmailTemplates.models import Template
from campaigns.models import Campaign, EmailLog

logger = logging.getLogger(__name__)

MAX_WORKERS = 5
MAX_RETRIES = 2
RETRY_DELAY = 2  # seconds between retries


# ─────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────

def _get_smtp_connection(account: emailUsers):
    """Build and return a configured SMTP connection for the given account."""
    host = account.email_host.lower().strip()
    port = account.email_port or 587
    use_tls = account.use_tls
    use_ssl = False

    # Auto-detect provider settings
    if 'zoho' in host:
        host = 'smtp.zoho.in' if host.endswith('.in') else 'smtp.zoho.com'
        port, use_ssl, use_tls = 465, True, False
    elif 'gmail' in host:
        host, port, use_tls, use_ssl = 'smtp.gmail.com', 587, True, False
    elif any(k in host for k in ['outlook', 'office365', 'live']):
        host, port, use_tls, use_ssl = 'smtp.office365.com', 587, True, False
    elif 'yahoo' in host:
        host, port, use_ssl, use_tls = 'smtp.mail.yahoo.com', 465, True, False
    elif any(k in host for k in ['icloud', 'me.com']):
        host, port, use_tls, use_ssl = 'smtp.mail.me.com', 587, True, False

    conn = get_connection(
        host=host, port=port,
        username=account.email_address,
        password=account.email_password,
        use_tls=False, use_ssl=False,
    )
    if use_ssl:
        conn.use_ssl = True
    elif use_tls:
        conn.use_tls = True
    return conn


def _replace_placeholders(text: str, recipient: Receipent) -> str:
    """Replace {{name}}, {{email}}, {{company}} placeholders in template body/subject."""
    replacements = {
        '{{name}}': recipient.name or 'Customer',
        '{name}': recipient.name or 'Customer',
        '{{email}}': recipient.email or '',
        '{email}': recipient.email or '',
        '{{company}}': getattr(recipient, 'receipent_category', '') or '',
        '{company}': getattr(recipient, 'receipent_category', '') or '',
    }
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, str(value))
    return text


def _inject_tracking_pixel(html_body: str, tracking_id: str, base_url: str) -> str:
    """Append a 1×1 tracking pixel before </body>."""
    pixel_url = f"{base_url}/tracking/open/{tracking_id}/"
    pixel = f'<img src="{pixel_url}" width="1" height="1" style="display:none" alt="" />'
    if '</body>' in html_body:
        return html_body.replace('</body>', f'{pixel}</body>')
    return html_body + pixel


def _rewrite_links_for_tracking(html_body: str, tracking_id: str, base_url: str) -> str:
    """Rewrite all <a href="..."> links to go through the click-tracking redirect."""
    def replace_link(match):
        original_url = match.group(1)
        # Skip mailto: and anchor links
        if original_url.startswith(('mailto:', '#', 'javascript:')):
            return match.group(0)
        import urllib.parse
        encoded = urllib.parse.quote(original_url, safe='')
        redirect_url = f"{base_url}/tracking/click/{tracking_id}/?url={encoded}"
        return f'href="{redirect_url}"'

    return re.sub(r'href="([^"]+)"', replace_link, html_body)


# ─────────────────────────────────────────────
# Core send function (single email, with retry)
# ─────────────────────────────────────────────

def _send_single_email(
    account: emailUsers,
    connection,
    log: EmailLog,
    subject: str,
    html_body: str,
    lock: threading.Lock,
    campaign: Campaign,
):
    """
    Send one email. Updates EmailLog and Campaign counters.
    Retries up to MAX_RETRIES on failure.
    """
    for attempt in range(MAX_RETRIES + 1):
        try:
            email_msg = EmailMessage(
                subject=subject,
                body=html_body,
                from_email=account.email_address,
                to=[log.recipient_email],
                connection=connection,
            )
            email_msg.content_subtype = "html"
            email_msg.send()

            # ── Success ──
            with lock:
                log.status = 'sent'
                log.sent_at = now()
                log.save(update_fields=['status', 'sent_at'])

                campaign.sent_count += 1
                campaign.pending_count = max(0, campaign.pending_count - 1)
                campaign.update_stats()

            logger.info(f"✅ Sent → {log.recipient_email}")
            return True

        except Exception as e:
            if attempt < MAX_RETRIES:
                logger.warning(f"Retry {attempt + 1} for {log.recipient_email}: {e}")
                time.sleep(RETRY_DELAY)
            else:
                # ── Final failure ──
                with lock:
                    log.status = 'failed'
                    log.error_message = str(e)[:500]
                    log.sent_at = now()
                    log.save(update_fields=['status', 'error_message', 'sent_at'])

                    campaign.failed_count += 1
                    campaign.pending_count = max(0, campaign.pending_count - 1)
                    campaign.update_stats()

                logger.error(f"❌ Failed → {log.recipient_email}: {e}")
                return False


# ─────────────────────────────────────────────
# Public API: create campaign + send bulk
# ─────────────────────────────────────────────

def send_bulk_email_campaign(
    user_id: int,
    selected_ids: list,
    campaign_name: str = None,
    base_url: str = 'http://127.0.0.1:8000',
    run_in_background: bool = False,
) -> Campaign:
    """
    Main entry point for bulk email sending.
    - Creates a Campaign record
    - If run_in_background=True, returns immediately and sends in a thread.
    """
    account = emailUsers.objects.get(id=user_id)
    recipients = Receipent.objects.filter(id__in=selected_ids, Sender=account)

    if not recipients.exists():
        raise ValueError("No valid recipients found.")

    template = Template.objects.filter(user=account, primary=True).first()
    if not template:
        raise ValueError("No primary template set. Please set a primary template first.")

    total = recipients.count()
    name = campaign_name or f"Campaign - {now().strftime('%Y-%m-%d %H:%M')}"

    # ── Create Campaign ──
    campaign = Campaign.objects.create(
        user=account,
        campaign_name=name,
        subject=template.subject,
        total_emails=total,
        pending_count=total,
        status='pending',
        template_id=template.id,
        email_body=template.body,
    )

    def _execute_campaign():
        try:
            _process_campaign_execution(account, recipients, template, campaign, base_url)
        except Exception as e:
            logger.error(f"Background campaign error: {e}")
            campaign.status = 'failed'
            campaign.save(update_fields=['status'])

    if run_in_background:
        thread = threading.Thread(target=_execute_campaign)
        thread.daemon = True # Ensure thread doesn't block exit
        thread.start()
        return campaign
    else:
        _execute_campaign()
        return campaign


def _process_campaign_execution(account, recipients, template, campaign, base_url):
    """Internal logic moved here to support both sync and async execution."""
    campaign.status = 'running'
    campaign.save(update_fields=['status'])
    
    total = recipients.count()

    # ── Pre-create all EmailLog records as pending ──
    logs = []
    for recipient in recipients:
        subject = _replace_placeholders(template.subject or '', recipient)
        html_body = _replace_placeholders(template.body or '', recipient)
        html_body = _inject_tracking_pixel(html_body, '', base_url)  # tracking_id set after log creation

        log = EmailLog(
            campaign=campaign,
            recipient_email=recipient.email,
            recipient_name=recipient.name,
            subject=subject,
            status='pending',
        )
        logs.append((log, recipient, subject))

    # Bulk create logs
    EmailLog.objects.bulk_create([l[0] for l in logs])

    # Re-fetch logs with their UUIDs
    created_logs = list(EmailLog.objects.filter(campaign=campaign).order_by('id'))

    # ── Build SMTP connection (shared) ──
    try:
        connection = _get_smtp_connection(account)
        connection.open()
    except Exception as e:
        campaign.status = 'failed'
        campaign.save(update_fields=['status'])
        logger.error(f"SMTP connection failed: {e}")
        raise

    lock = threading.Lock()

    # ── Prepare send tasks ──
    def make_task(log_obj, recipient):
        subject_text = _replace_placeholders(template.subject or '', recipient)
        html_body = _replace_placeholders(template.body or '', recipient)
        html_body = _inject_tracking_pixel(html_body, str(log_obj.tracking_id), base_url)
        html_body = _rewrite_links_for_tracking(html_body, str(log_obj.tracking_id), base_url)
        return log_obj, subject_text, html_body

    tasks = []
    for i, (_, recipient, _) in enumerate(logs):
        if i < len(created_logs):
            task = make_task(created_logs[i], recipient)
            tasks.append(task)

    # ── Send in parallel ──
    # Dynamic worker allocation:
    # - If <= 10 emails: use 1 worker (single thread)
    # - If > 10 emails: scale up to MAX_WORKERS (5)
    num_workers = 1
    if total > 10:
        num_workers = min(MAX_WORKERS, (total // 10) + 1)
    
    logger.info(f"🚀 Starting bulk send for {total} emails using {num_workers} threads...")

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {
            executor.submit(
                _send_single_email,
                account, connection, log_obj, subject_text, html_body, lock, campaign
            ): log_obj.recipient_email
            for log_obj, subject_text, html_body in tasks
        }
        for future in as_completed(futures):
            email_addr = futures[future]
            try:
                future.result()
            except Exception as exc:
                logger.error(f"Unhandled exception for {email_addr}: {exc}")

    # ── Finalize campaign ──
    try:
        connection.close()
    except Exception:
        pass

    campaign.refresh_from_db()
    campaign.status = 'completed'
    campaign.completed_at = now()
    if campaign.total_emails > 0:
        campaign.success_rate = round(campaign.sent_count / campaign.total_emails * 100, 2)
    campaign.save(update_fields=['status', 'completed_at', 'success_rate'])

    # Update recipient send_time counters
    recipients.update()
    for r in recipients:
        r.send_time += 1
        r.save(update_fields=['send_time'])

    # Update template usage count
    template.no_of_time_used += total
    template.save(update_fields=['no_of_time_used'])

    logger.info(
        f"Campaign '{campaign.campaign_name}' completed: "
        f"{campaign.sent_count} sent, {campaign.failed_count} failed."
    )
    return campaign


# ─────────────────────────────────────────────
# Backward-compat wrapper (used by old views)
# ─────────────────────────────────────────────

def send_bulk_email(user_id: int, selected_ids: list) -> bool:
    """Legacy wrapper — keeps old view code working."""
    try:
        send_bulk_email_campaign(user_id, selected_ids)
        return True
    except Exception as e:
        logger.error(f"send_bulk_email legacy wrapper error: {e}")
        return False
