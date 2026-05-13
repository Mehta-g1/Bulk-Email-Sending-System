from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from .services import send_otp, verify_otp


@csrf_exempt
@require_POST
def send_otp_view(request):
    """Web view: POST {email, purpose} → sends OTP."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        data = request.POST

    email = data.get('email', '').strip()
    purpose = data.get('purpose', 'general')

    if not email:
        return JsonResponse({'success': False, 'message': 'Email is required.'}, status=400)

    result = send_otp(email, purpose)
    status_code = 200 if result['success'] else 500
    return JsonResponse(result, status=status_code)


@csrf_exempt
@require_POST
def verify_otp_view(request):
    """Web view: POST {email, otp, purpose} → verify OTP."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        data = request.POST

    email = data.get('email', '').strip()
    otp_code = data.get('otp', '').strip()
    purpose = data.get('purpose', 'general')

    if not email or not otp_code:
        return JsonResponse({'success': False, 'message': 'Email and OTP are required.'}, status=400)

    result = verify_otp(email, otp_code, purpose)
    status_code = 200 if result['success'] else 400
    return JsonResponse(result, status=status_code)
