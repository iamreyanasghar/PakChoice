from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import TemplateView
from django.views.static import serve as static_serve
import os

urlpatterns = [
    path('robots.txt', static_serve, {'document_root': settings.BASE_DIR / 'static', 'path': 'robots.txt'}),
    path('', include('core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
