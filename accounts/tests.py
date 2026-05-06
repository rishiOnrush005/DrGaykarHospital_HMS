from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import StaffCreationForm


User = get_user_model()


class StaffSecurityTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create_user(
            username='doctor',
            password='StrongPass123!',
            role='doctor',
        )
        self.staff = User.objects.create_user(
            username='staff',
            password='StrongPass123!',
            role='staff',
        )
        self.client.force_login(self.doctor)

    def test_delete_staff_requires_post(self):
        url = reverse('delete_staff', args=[self.staff.pk])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 405)
        self.assertTrue(User.objects.filter(pk=self.staff.pk).exists())

    def test_delete_staff_allows_post(self):
        url = reverse('delete_staff', args=[self.staff.pk])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=self.staff.pk).exists())

    def test_staff_creation_uses_password_validators(self):
        form = StaffCreationForm(data={
            'username': 'newstaff',
            'first_name': 'New',
            'last_name': 'Staff',
            'phone': '9876543210',
            'password': '1234',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)
