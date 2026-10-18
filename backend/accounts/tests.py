from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

class AccountsTests(APITestCase):
    def setUp(self):
        self.signup_url = reverse('auth_signup')
        self.login_url = reverse('auth_login')
        self.user_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }

    def test_user_signup_success(self):
        response = self.client.post(self.signup_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], "Signup successful. Please log in.")
        self.assertTrue(User.objects.filter(email='john@example.com').exists())

    def test_user_signup_password_mismatch(self):
        bad_data = self.user_data.copy()
        bad_data['confirm_password'] = 'differentpassword'
        response = self.client.post(self.signup_url, bad_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirm_password', response.data)

    def test_user_login_success(self):
        # Create a user first
        self.client.post(self.signup_url, self.user_data, format='json')
        
        login_data = {
            'email': 'john@example.com',
            'password': 'password123'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['name'], 'John Doe')
        self.assertEqual(response.data['user']['email'], 'john@example.com')

