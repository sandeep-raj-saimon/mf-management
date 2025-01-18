from rest_framework.test import APITestCase
from rest_framework import status
from .models import *

class UserRegistrationTestCase(APITestCase):
    def test_user_registration(self):
        url = "http://127.0.0.1:8000/api/user/register/"
        data = {
            "email": "testuser@example.com",
            "password": "securepassword123"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

class UserLoginTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="testuser@example.com", password="securepassword123")

    def test_user_login(self):
        url = "http://127.0.0.1:8000/api/user/login/"
        data = {
            "email": "testuser@example.com",
            "password": "securepassword123"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
