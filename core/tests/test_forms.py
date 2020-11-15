from mixer.backend.django import mixer
from django.contrib.auth.hashers import check_password
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



class UpdatePasswordFormTests(TestCase):

    def test_form_can_update_password(self):
        john = mixer.blend(User, email="john@gmail.com")
        john.set_password("password")
        form = UpdatePasswordForm({"current": "password", "new": "warwick96"}, instance=john)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertTrue(check_password("warwick96", john.password))
    

    def test_form_can_reject_current_password(self):
        john = mixer.blend(User, email="john@gmail.com")
        john.set_password("password")
        form = UpdatePasswordForm({"current": "xxxxxxxxx", "new": "warwick96"}, instance=john)
        self.assertFalse(form.is_valid())
        self.assertIn("password not correct", form.errors["current"][0])
    

    def test_form_can_reject_new_password(self):
        john = mixer.blend(User, email="john@gmail.com")
        john.set_password("password")
        form = UpdatePasswordForm({"current": "password", "new": "arwick96"}, instance=john)
        self.assertFalse(form.is_valid())
        self.assertIn("9 characters", form.errors["new"][0])
        form = UpdatePasswordForm({"current": "password", "new": "3738426578326"}, instance=john)
        self.assertFalse(form.is_valid())
        self.assertIn("numeric", form.errors["new"][0])
        form = UpdatePasswordForm({"current": "password", "new": "password1"}, instance=john)
        self.assertFalse(form.is_valid())
        self.assertIn("too common", form.errors["new"][0])