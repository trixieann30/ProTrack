from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_notificationpreference'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notificationpreference',
            name='daily_digest',
        ),
        migrations.RemoveField(
            model_name='notificationpreference',
            name='weekly_digest',
        ),
    ]