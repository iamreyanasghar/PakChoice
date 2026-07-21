# This migration is now a no-op. The fields it previously added
# (is_active, deleted_at, updated_at) are already created by migration 0001.
# Kept as an empty migration to preserve migration history for existing databases.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_add_soft_delete_and_audit_fields'),
    ]

    operations = []
