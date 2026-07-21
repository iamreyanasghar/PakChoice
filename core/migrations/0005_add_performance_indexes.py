# Performance indexes for common filter queries.
# These speed up the home page and admin list views that filter by
# verified/status/is_active combinations.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_add_alternativevote_created_at'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='boycottproduct',
            index=models.Index(fields=['verified', 'is_active'], name='idx_product_verified_active'),
        ),
        migrations.AddIndex(
            model_name='pakistanialternative',
            index=models.Index(fields=['status', 'is_active'], name='idx_alternative_status_active'),
        ),
    ]
