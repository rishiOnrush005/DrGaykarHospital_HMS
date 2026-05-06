import uuid

import backup.models
from django.contrib.auth.hashers import identify_hasher, make_password
from django.db import migrations, models


def hash_legacy_security_pins(apps, schema_editor):
    BackupSettings = apps.get_model('backup', 'BackupSettings')
    for settings_obj in BackupSettings.objects.all():
        pin = settings_obj.security_pin or ''
        try:
            identify_hasher(pin)
        except ValueError:
            settings_obj.security_pin = make_password(pin if len(pin) == 4 and pin.isdigit() else '5741')
            settings_obj.pin_version = uuid.uuid4()
            settings_obj.save(update_fields=['security_pin', 'pin_version'])


class Migration(migrations.Migration):

    dependencies = [
        ('backup', '0002_backupsettings_security_pin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='backupsettings',
            name='security_pin',
            field=models.CharField(
                default=backup.models.default_security_pin_hash,
                max_length=128,
                verbose_name='Security PIN',
            ),
        ),
        migrations.AddField(
            model_name='backupsettings',
            name='pin_version',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.RunPython(hash_legacy_security_pins, migrations.RunPython.noop),
    ]
