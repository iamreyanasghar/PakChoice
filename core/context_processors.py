from .models import Alternative


def moderation_context(request):
    if request.user.is_authenticated and request.user.is_staff:
        return {'pending_count': Alternative.objects.filter(status='pending').count()}
    return {'pending_count': 0}
