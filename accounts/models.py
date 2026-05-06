from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('doctor', _('Doctor')),
        ('staff', _('Staff')),
    )
    LANGUAGE_CHOICES = (
        ('en', 'English'),
        ('mr', 'Marathi'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    phone = models.CharField(max_length=15, blank=True, null=True)
    language_preference = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
