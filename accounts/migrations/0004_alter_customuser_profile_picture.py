# accounts/migrations/0004_alter_customuser_profile_picture.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_customuser_program'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='profile_picture',
            field=models.URLField(
                blank=True,
                null=True,
                max_length=500,
                help_text='URL to profile picture in Supabase storage'
            ),
        ),
    ]