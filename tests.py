from django.test import TestCase
from django.urls import reverse


class AuthenticationTests(TestCase):
    def test_root_redirects_to_login(self):
        response = self.client.get('/')
        self.assertRedirects(response, reverse('accounts:login'))

    def test_login_redirects_to_dashboard(self):
        from django.contrib.auth import get_user_model
        get_user_model().objects.create_user(username='admin@example.com', password='Strong-password-123')
        response = self.client.post(reverse('accounts:login'), {'username': 'admin@example.com', 'password': 'Strong-password-123'})
        self.assertRedirects(response, reverse('dashboard:index'))
