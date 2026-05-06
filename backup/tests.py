import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import BackupSettings


User = get_user_model()


class BackupSecurityTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.allowed_root = Path(self.temp_dir.name)
        self.settings_override = override_settings(
            BACKUP_ALLOWED_ROOTS=[self.allowed_root],
            BACKUP_MAX_UPLOAD_SIZE=1024 * 1024,
        )
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

        self.doctor = User.objects.create_user(
            username='doctor',
            password='StrongPass123!',
            role='doctor',
        )
        self.client.force_login(self.doctor)

    def _verified_backup_settings(self, pin='0101'):
        config = BackupSettings.get_settings()
        config.backup_path = str(self.allowed_root)
        config.set_security_pin(pin)
        config.save(update_fields=['backup_path', 'security_pin', 'pin_version'])

        session = self.client.session
        session['security_pin_verified'] = True
        session['security_pin_version'] = str(config.pin_version)
        session.save()
        return config

    def test_legacy_plaintext_pin_is_upgraded_to_hash(self):
        BackupSettings.objects.update_or_create(
            id=1,
            defaults={
                'backup_path': str(self.allowed_root),
                'security_pin': '0101',
            },
        )

        config = BackupSettings.get_settings()

        self.assertNotEqual(config.security_pin, '0101')
        self.assertTrue(config.check_security_pin('0101'))

    def test_verify_pin_does_not_redirect_to_external_next_url(self):
        self._verified_backup_settings()

        response = self.client.post(
            f"{reverse('verify_pin')}?next=https://evil.example/",
            {'pin': '0101'},
        )

        self.assertRedirects(response, reverse('backup_manager'), fetch_redirect_response=False)

    def test_backup_path_must_stay_under_allowed_root(self):
        config = self._verified_backup_settings()
        outside_path = self.allowed_root.parent / 'outside-backups'

        response = self.client.post(reverse('backup_manager'), {
            'action': 'update_path',
            'backup_path': str(outside_path),
        })

        config.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(config.backup_path, str(self.allowed_root))

    def test_restore_rejects_non_sqlite_content(self):
        self._verified_backup_settings()
        upload = SimpleUploadedFile(
            'backup.sqlite3',
            b'not a sqlite database',
            content_type='application/octet-stream',
        )

        response = self.client.post(reverse('restore_database'), {'backup_file': upload})

        self.assertEqual(response.status_code, 200)
