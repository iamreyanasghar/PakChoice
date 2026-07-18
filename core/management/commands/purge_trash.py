"""
Management command to permanently delete items from trash older than 10 days.
Run this daily via cron or a task scheduler.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Category, SubCategory, BoycottProduct, PakistaniAlternative
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Permanently delete soft-deleted items older than 10 days from trash'

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=10)

        models_to_purge = [
            (Category, 'categories'),
            (SubCategory, 'subcategories'),
            (BoycottProduct, 'products'),
            (PakistaniAlternative, 'alternatives'),
            (User, 'users'),
        ]

        total_purged = 0
        for model, name in models_to_purge:
            if name == 'users':
                deleted_count, _ = model.objects.filter(is_active=False).delete()
            else:
                deleted_count, _ = model.objects.filter(
                    is_active=False,
                    deleted_at__lt=cutoff
                ).delete()
            total_purged += deleted_count
            self.stdout.write(
                self.style.SUCCESS(f'Purged {deleted_count} {name} older than 10 days')
            )

        self.stdout.write(
            self.style.SUCCESS(f'Total items purged: {total_purged}')
        )
