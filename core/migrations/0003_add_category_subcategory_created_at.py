# Fix for database tables that were created from an older schema while
# migration 0001 was marked as applied. The Category and SubCategory tables
# were missing the created_at column that the models define. This migration
# adds it so the database matches the model definitions.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_add_missing_audit_columns'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AddField(
            model_name='subcategory',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
