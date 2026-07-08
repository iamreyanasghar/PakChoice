from .models import PakistaniAlternative


def moderation_context(request):
    if request.user.is_authenticated and request.user.is_staff:
        return {'pending_count': PakistaniAlternative.objects.filter(status='pending').count()}
    return {'pending_count': 0}
