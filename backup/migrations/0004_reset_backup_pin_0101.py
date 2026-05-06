import uuid

from django.contrib.auth.hashers import make_password
from django.db import migrations


def reset_backup_pin(apps, schema_editor):
    BackupSettings = apps.get_model('backup', 'BackupSettings')
    settings_obj, _ = BackupSettings.objects.get_or_create(id=1)
    settings_obj.security_pin = make_password('0101')
    settings_obj.pin_version = uuid.uuid4()
    settings_obj.save(update_fields=['security_pin', 'pin_version'])


class Migration(migrations.Migration):

    dependencies = [
        ('backup', '0003_hash_security_pin_and_pin_version'),
    ]

    operations = [
        migrations.RunPython(reset_backup_pin, migrations.RunPython.noop),
    ]
