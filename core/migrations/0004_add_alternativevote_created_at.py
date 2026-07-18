# Fix for database tables that were created from an older schema while
# migration 0001 was marked as applied. The AlternativeVote table was
# missing the created_at column that the model defines. This migration
# adds it so the database matches the model definition.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_add_category_subcategory_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='alternativevote',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
