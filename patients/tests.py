from django.test import TestCase, Client
from django.urls import reverse
from .models import Patient
import uuid
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

User = get_user_model()

class PatientTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password', role='staff')
        self.client = Client()
        self.client.login(username='testuser', password='password')

    def test_patient_id_generation(self):
        p1 = Patient.objects.create(name='Test 1', age=30, gender='M', phone='1234567890')
        p2 = Patient.objects.create(name='Test 2', age=25, gender='F', phone='0987654321')
        
        self.assertEqual(p1.patient_id, 'PAT-0001')
        self.assertEqual(p2.patient_id, 'PAT-0002')
        self.assertTrue(isinstance(p1.uuid, uuid.UUID))
        self.assertTrue(isinstance(p2.uuid, uuid.UUID))

    def test_csv_import_atomic(self):
        csv_content = b"Name,Age,Gender,Phone,Village,Blood Group\nJohn,40,M,111,Village1,O+\nJane,invalid_age,F,222,Village2,A+\n"
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")
        
        response = self.client.post(reverse('import_patients_csv'), {'csv_file': csv_file})
            
        # Ensure that no patients were created due to transaction.atomic()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Patient.objects.count(), 0)

    def test_csv_export_escapes_spreadsheet_formula_values(self):
        Patient.objects.create(
            name='=HYPERLINK("https://evil.example")',
            age=30,
            gender='M',
            phone='+1234567890',
            village='@Village',
            blood_group='O+',
        )

        response = self.client.get(reverse('export_patients_csv'))
        content = response.content.decode('utf-8')

        self.assertIn('\'=HYPERLINK', content)
        self.assertIn('\'+1234567890', content)
        self.assertIn('\'@Village', content)
