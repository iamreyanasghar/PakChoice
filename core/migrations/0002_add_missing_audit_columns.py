# Fix for database tables that were created from an older schema while
# migration 0001 was marked as applied. The following columns were missing
# from the actual tables: is_active, deleted_at, updated_at.
# This migration adds them so the database matches the model definitions.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_add_soft_delete_and_audit_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='boycottproduct',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='boycottproduct',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='boycottproduct',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='category',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='category',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='category',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='subcategory',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='subcategory',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='subcategory',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='pakistanialternative',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pakistanialternative',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='pakistanialternative',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
