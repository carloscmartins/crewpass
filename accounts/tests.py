from django.test import TestCase
from django.urls import reverse

from .models import User


class EmailLoginTests(TestCase):
    def setUp(self):
        self.password = 'Test-password-23!'
        self.user = User.objects.create_user(
            email='operator@example.com',
            password=self.password,
        )

    def test_user_authenticates_with_email(self):
        response = self.client.post(
            reverse('accounts:login'),
            {'username': self.user.email, 'password': self.password},
        )

        self.assertRedirects(response, reverse('organizations:dashboard'))

    def test_invalid_password_does_not_authenticate(self):
        response = self.client.post(
            reverse('accounts:login'),
            {'username': self.user.email, 'password': 'wrong-password'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
