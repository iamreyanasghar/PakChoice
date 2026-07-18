"""
Custom decorators for rate limiting and security.
"""
from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import functools


def rate_limit(key_prefix, limit=10, period=60):
    """
    Rate limiting decorator.
    Limits requests per IP address or authenticated user.
    
    Args:
        key_prefix: Prefix for the cache key
        limit: Maximum number of requests allowed
        period: Time period in seconds
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                ip_address = request.META.get('REMOTE_ADDR', 'unknown')
            else:
                ip_address = f"user_{request.user.id}"
            
            cache_key = f"rate_limit_{key_prefix}_{ip_address}"
            request_count = cache.get(cache_key, 0)
            
            if request_count >= limit:
                if request.content_type == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse(
                        {'error': 'Too many requests. Please try again later.'},
                        status=429
                    )
                from django.shortcuts import redirect
                from django.contrib import messages
                messages.error(request, 'Too many requests. Please try again later.')
                return redirect('home')
            
            # Increment counter and set expiry
            cache.set(cache_key, request_count + 1, period)
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator
