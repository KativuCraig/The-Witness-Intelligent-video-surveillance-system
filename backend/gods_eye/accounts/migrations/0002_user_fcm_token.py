# Adds FCM device token for companion app (Ionic) push alerts

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='fcm_device_token',
            field=models.TextField(
                blank=True,
                default='',
                help_text='FCM registration token for the companion mobile app (push alerts)',
            ),
        ),
    ]
