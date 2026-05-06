import uuid

from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.crypto import constant_time_compare
from django.utils.translation import gettext_lazy as _


def default_security_pin_hash():
    return make_password('0101')


class BackupSettings(models.Model):
    # Only one instance of this model should exist
    backup_path = models.CharField(_("Backup Storage Path"), max_length=500, default='/data/data/com.termux/files/home/backups/')
    last_backup_date = models.DateTimeField(_("Last Backup Date"), null=True, blank=True)
    auto_backup_days = models.IntegerField(_("Auto Backup Frequency (Days)"), default=10)
    security_pin = models.CharField(_("Security PIN"), max_length=128, default=default_security_pin_hash)
    pin_version = models.UUIDField(default=uuid.uuid4, editable=False)

    class Meta:
        verbose_name = _("Backup Settings")
        verbose_name_plural = _("Backup Settings")

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(id=1)
        if obj.has_legacy_plaintext_pin():
            obj.set_security_pin(obj.security_pin)
            obj.save(update_fields=['security_pin', 'pin_version'])
        return obj

    def has_legacy_plaintext_pin(self):
        return len(self.security_pin or '') == 4 and self.security_pin.isdigit()

    def check_security_pin(self, raw_pin):
        raw_pin = str(raw_pin or '')
        if len(raw_pin) != 4 or not raw_pin.isdigit():
            return False

        if self.has_legacy_plaintext_pin():
            return constant_time_compare(raw_pin, self.security_pin)

        return check_password(raw_pin, self.security_pin)

    def set_security_pin(self, raw_pin):
        raw_pin = str(raw_pin or '')
        if len(raw_pin) != 4 or not raw_pin.isdigit():
            raise ValidationError(_("PIN must be exactly 4 digits."))

        self.security_pin = make_password(raw_pin)
        self.pin_version = uuid.uuid4()

    def __str__(self):
        return f"Backup Settings (Last: {self.last_backup_date})"
