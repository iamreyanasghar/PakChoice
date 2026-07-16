"""
Security event logging utility.
"""
import logging
from django.utils import timezone

security_logger = logging.getLogger('django.security')


def log_security_event(event_type, message, user=None, request=None, extra_data=None):
    """
    Log a security event.
    
    Args:
        event_type: Type of event (e.g., 'login_failed', 'account_locked', 'account_deleted')
        message: Human-readable message
        user: User instance (optional)
        request: HttpRequest instance (optional)
        extra_data: Additional data to log (optional)
    """
    extra = {
        'event_type': event_type,
        'timestamp': timezone.now().isoformat(),
    }
    
    if user:
        extra['user_id'] = user.id
        extra['username'] = user.username
    
    if request:
        extra['ip_address'] = request.META.get('REMOTE_ADDR', 'unknown')
        extra['user_agent'] = request.META.get('HTTP_USER_AGENT', 'unknown')
    
    if extra_data:
        extra.update(extra_data)
    
    security_logger.info(f"{event_type}: {message}", extra=extra)
