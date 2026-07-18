"""
Custom middleware for cache headers and security headers.
"""

import time
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


class CacheControlMiddleware(MiddlewareMixin):
    """
    Add cache headers for static files and other optimizations.
    """
    def process_response(self, request, response):
        # Cache static files for 1 year (immutable)
        if request.path.startswith('/static/'):
            response['Cache-Control'] = 'public, max-age=31536000, immutable'
            response['Expires'] = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time() + 31536000))
        
        # Cache media files (user avatars) for 1 day
        elif request.path.startswith('/media/'):
            response['Cache-Control'] = 'public, max-age=86400'
            response['Expires'] = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time() + 86400))
        
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses.
    """
    def process_response(self, request, response):
        # Content Security Policy
        # Note: 'unsafe-inline' is kept for Tailwind CDN styles.
        # Remove when Tailwind is built into the static pipeline.
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https: http:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        # Permissions Policy
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Referrer Policy (also set in settings, but ensuring it's here too)
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
