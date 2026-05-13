"""
OTP Service — generate, send, verify OTPs.
Reusable by both web views and API endpoints.
"""
import random
import string
import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from .models import OTPVerification

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5
OTP_EXPIRY_MINUTES = 10


def generate_otp(length=6) -> str:
    """Generate a secure numeric OTP."""
    return ''.join(random.choices(string.digits, k=length))


def create_otp(email: str, purpose: str = 'general') -> OTPVerification:
    """
    Invalidate any existing active OTPs for this email+purpose,
    then create a fresh one.
    """
    # Invalidate old ones
    OTPVerification.objects.filter(
        email=email,
        purpose=purpose,
        is_verified=False,
    ).update(expiry_time=timezone.now())

    otp_code = generate_otp()
    record = OTPVerification.objects.create(
        email=email,
        otp=otp_code,
        purpose=purpose,
    )
    logger.info(f"OTP created for {email} [{purpose}]")
    return record


def send_otp_email(email: str, otp_code: str, purpose: str = 'general') -> bool:
    """Send OTP via the platform's default SMTP (settings email)."""
    subject = "Your OTP Verification Code"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [email]

    html_content = f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background:#f4f6f9; margin:0; padding:0;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9; padding:40px 0;">
        <tr><td align="center">
          <table width="480" cellpadding="0" cellspacing="0"
                 style="background:#ffffff; border-radius:12px; overflow:hidden;
                        box-shadow:0 4px 24px rgba(0,0,0,0.08);">
            <tr>
              <td style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
                          padding:32px; text-align:center;">
                <h1 style="color:#ffffff; margin:0; font-size:24px; font-weight:700;">
                  🔐 OTP Verification
                </h1>
              </td>
            </tr>
            <tr>
              <td style="padding:40px 36px;">
                <p style="color:#374151; font-size:15px; margin:0 0 24px;">
                  Your One-Time Password for <strong>{purpose}</strong> is:
                </p>
                <div style="text-align:center; margin:24px 0;">
                  <span style="display:inline-block; background:#f3f0ff;
                                border:2px dashed #764ba2; border-radius:10px;
                                padding:18px 40px; font-size:38px;
                                font-weight:800; letter-spacing:12px;
                                color:#5b21b6;">
                    {otp_code}
                  </span>
                </div>
                <p style="color:#6b7280; font-size:13px; margin:24px 0 0;">
                  ⏱ This OTP expires in <strong>{OTP_EXPIRY_MINUTES} minutes</strong>.<br>
                  Do not share this code with anyone.
                </p>
              </td>
            </tr>
            <tr>
              <td style="background:#f9fafb; padding:20px 36px; text-align:center;
                          border-top:1px solid #e5e7eb;">
                <p style="color:#9ca3af; font-size:12px; margin:0;">
                  Email Automation Platform · If you did not request this, ignore this email.
                </p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """

    try:
        msg = EmailMultiAlternatives(subject, f"Your OTP is: {otp_code}", from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        logger.info(f"OTP email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP to {email}: {e}")
        return False


def send_otp(email: str, purpose: str = 'general') -> dict:
    """
    Public API: create OTP + send email.
    Returns: {'success': bool, 'message': str}
    """
    record = create_otp(email, purpose)
    sent = send_otp_email(email, record.otp, purpose)

    if sent:
        return {'success': True, 'message': f'OTP sent to {email}'}
    else:
        return {'success': False, 'message': 'Failed to send OTP email. Check SMTP settings.'}


def verify_otp(email: str, otp_code: str, purpose: str = 'general') -> dict:
    """
    Verify OTP submitted by user.
    Returns: {'success': bool, 'message': str}
    """
    try:
        record = OTPVerification.objects.filter(
            email=email,
            purpose=purpose,
            is_verified=False,
        ).latest('created_at')
    except OTPVerification.DoesNotExist:
        return {'success': False, 'message': 'No active OTP found. Please request a new one.'}

    if record.is_expired():
        return {'success': False, 'message': 'OTP has expired. Please request a new one.'}

    if record.is_max_attempts():
        return {'success': False, 'message': 'Too many failed attempts. Request a new OTP.'}

    record.attempts += 1

    if record.otp != otp_code:
        record.save()
        remaining = MAX_ATTEMPTS - record.attempts
        return {'success': False, 'message': f'Invalid OTP. {remaining} attempt(s) remaining.'}

    record.is_verified = True
    record.save()
    logger.info(f"OTP verified for {email} [{purpose}]")
    return {'success': True, 'message': 'OTP verified successfully.'}
