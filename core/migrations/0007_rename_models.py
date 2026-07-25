from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0006_make_alternativevote_user_nullable'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='BoycottProduct',
            new_name='Product',
        ),
        migrations.RenameModel(
            old_name='PakistaniAlternative',
            new_name='Alternative',
        ),
        migrations.RenameModel(
            old_name='AlternativeVote',
            new_name='Vote',
        ),
    ]
