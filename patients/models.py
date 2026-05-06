import uuid
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

class Patient(models.Model):
    GENDER_CHOICES = (
        ('M', _('Male')),
        ('F', _('Female')),
        ('O', _('Other')),
    )
    
    # Primary identifiers with indexing for sub-1-second search
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    patient_id = models.CharField(_("Patient ID"), max_length=20, unique=True, editable=False, db_index=True)
    name = models.CharField(_("Name"), max_length=255, db_index=True)
    phone = models.CharField(_("Phone"), max_length=15, blank=True, null=True, db_index=True)
    
    # Practical fields for rural use
    age = models.IntegerField(_("Age"))
    gender = models.CharField(_("Gender"), max_length=1, choices=GENDER_CHOICES)
    village = models.CharField(_("Village/Area"), max_length=100, blank=True, null=True, db_index=True)
    blood_group = models.CharField(_("Blood Group"), max_length=5, blank=True, null=True)
    
    registered_on = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.patient_id:
            with transaction.atomic():
                last_patient = Patient.objects.select_for_update().order_by('id').last()
                if not last_patient:
                    self.patient_id = 'PAT-0001'
                else:
                    last_id = int(last_patient.patient_id.split('-')[1])
                    self.patient_id = f'PAT-{str(last_id + 1).zfill(4)}'
                super(Patient, self).save(*args, **kwargs)
        else:
            super(Patient, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient_id} - {self.name} ({self.village})"
