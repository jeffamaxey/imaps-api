from django.test import TestCase
from core.forms import *

class SignupFormTests(TestCase):

    def test_signup_form_uses_password(self):
        form = SignupForm({
            "name": "Johnny", "email": "a@b.co",
            "username": "john", "password": "sw0rdfish123"
        })
        self.assertTrue(form.is_valid())
        form.save()
        self.assertNotEqual(form.instance.password, "sw0rdfish123")
    

    def test_signup_form_validates_password(self):
        form = SignupForm({
            "name": "Johnny", "email": "a@b.co",
            "username": "john", "password": "328746327869423"
        })
        self.assertFalse(form.is_valid())
        self.assertIn("numeric", form.errors["password"][0])

        form = SignupForm({
            "name": "Johnny", "email": "a@b.co",
            "username": "john", "password": "sddsd78"
        })
        self.assertFalse(form.is_valid())
        self.assertIn("9 characters", form.errors["password"][0])

        form = SignupForm({
            "name": "Johnny", "email": "a@b.co",
            "username": "john", "password": "password123"
        })
        self.assertFalse(form.is_valid())
        self.assertIn("too common", form.errors["password"][0])