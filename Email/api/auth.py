"""
api/auth.py — API Key authentication.

Usage (in api views):
    from api.auth import api_key_required

    @api_key_required
    def my_view(request):
        user = request.api_user   # the authenticated emailUsers instance
        ...

The client sends:
    Authorization: Bearer <API_KEY>
"""
import functools
import logging
from django.http import JsonResponse
from CreateUser.models import emailUsers

logger = logging.getLogger(__name__)


def get_api_user(request):
    """
    Extract and validate API key from Authorization header.
    Returns (user, error_response).
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None, JsonResponse(
            {'error': 'Missing or invalid Authorization header. Use: Bearer <API_KEY>'},
            status=401
        )

    api_key = auth_header[len('Bearer '):].strip()
    if not api_key:
        return None, JsonResponse({'error': 'API key is empty.'}, status=401)

    try:
        user = emailUsers.objects.get(api_key=api_key)
    except emailUsers.DoesNotExist:
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        return None, JsonResponse({'error': 'Invalid API key.'}, status=401)

    # Track usage
    user.api_usage_count = (user.api_usage_count or 0) + 1
    user.save(update_fields=['api_usage_count'])

    return user, None


def api_key_required(view_func):
    """Decorator: validates API key and sets request.api_user."""
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user, error = get_api_user(request)
        if error:
            return error
        request.api_user = user
        return view_func(request, *args, **kwargs)
    return wrapper
