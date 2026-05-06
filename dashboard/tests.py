from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class DashboardSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='staff',
            password='StrongPass123!',
            role='staff',
        )
        self.client.force_login(self.user)

    def test_language_preference_ignores_external_referer(self):
        response = self.client.post(
            reverse('set_language_pref'),
            {'language': 'en'},
            HTTP_REFERER='https://evil.example/',
        )

        self.assertRedirects(response, reverse('dashboard'), fetch_redirect_response=False)
