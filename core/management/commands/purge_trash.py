"""
Management command to permanently delete items from trash older than 10 days.
This can be run manually, via cron, or is executed automatically once per day
by the built-in scheduler started in core/apps.py (no external dependencies).
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Category, SubCategory, BoycottProduct, PakistaniAlternative
from django.contrib.auth import get_user_model
User = get_user_model()

logger = logging.getLogger(__name__)

# Models that support soft-delete via is_active / deleted_at.
MODELS_TO_PURGE = [
    (Category, 'categories'),
    (SubCategory, 'subcategories'),
    (BoycottProduct, 'products'),
    (PakistaniAlternative, 'alternatives'),
    (User, 'users'),
]


def purge_trash(cutoff=None):
    """Permanently delete soft-deleted items older than the cutoff.

    Returns the total number of items purged. Safe to call repeatedly;
    the operation is idempotent because already-purged rows are gone.
    """
    if cutoff is None:
        cutoff = timezone.now() - timedelta(days=10)

    total_purged = 0
    for model, name in MODELS_TO_PURGE:
        if name == 'users':
            deleted_count, _ = model.objects.filter(is_active=False).delete()
        else:
            deleted_count, _ = model.objects.filter(
                is_active=False,
                deleted_at__lt=cutoff
            ).delete()
        total_purged += deleted_count
        logger.info('Purged %s %s older than 10 days', deleted_count, name)
    return total_purged


class Command(BaseCommand):
    help = 'Permanently delete soft-deleted items older than 10 days from trash'

    def handle(self, *args, **options):
        total_purged = purge_trash()
        self.stdout.write(
            self.style.SUCCESS(f'Total items purged: {total_purged}')
        )
