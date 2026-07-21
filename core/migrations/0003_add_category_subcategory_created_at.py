# This migration is now a no-op. The created_at field it previously added
# is already created by migration 0001. Kept as an empty migration to
# preserve migration history for existing databases.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_add_missing_audit_columns'),
    ]

    operations = []
