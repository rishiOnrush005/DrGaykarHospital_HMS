import uuid
from django.db import models
from patients.models import Patient
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class PrescriptionTemplate(models.Model):
    name = models.CharField(_("Template Name"), max_length=100) # e.g. "Viral Fever"
    content = models.TextField(_("Medication Details")) # e.g. "Tab. PCM 500mg..."
    
    def __str__(self):
        return self.name

class Visit(models.Model):
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('unexamined', _('Unexamined')),
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='visits', verbose_name=_("Patient"))
    visited_on = models.DateTimeField(_("Visited On"), auto_now_add=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Vitals
    weight = models.DecimalField(_("Weight"), max_digits=5, decimal_places=2, null=True, blank=True)
    bp = models.CharField(_("BP"), max_length=20, null=True, blank=True)
    temp = models.CharField(_("Temp"), max_length=10, null=True, blank=True)
    sugar = models.CharField(_("Sugar"), max_length=20, null=True, blank=True)

    # Clinical
    symptoms = models.TextField(_("Symptoms"))
    diagnosis = models.TextField(_("Diagnosis"))
    prescription_text = models.TextField(_("Prescription"))
    prescription_photo = models.ImageField(_("Prescription Photo"), upload_to='prescriptions/', blank=True, null=True)
    follow_up_date = models.DateField(_("Follow-up Date"), null=True, blank=True)
    
    attended_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name=_("Attended By"))

    def __str__(self):
        return f"{self.patient.name} - {self.visited_on.date()}"
