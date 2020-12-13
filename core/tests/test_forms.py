import os
from mixer.backend.django import mixer
from django.contrib.auth.hashers import check_password
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
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



class UpdateImageFormTests(TestCase):

    def setUp(self):
        self.files_at_start = os.listdir("uploads")

    
    def tearDown(self):
        for f in os.listdir("uploads"):
            if f not in self.files_at_start:
                if os.path.exists(os.path.join("uploads", f)):
                    os.remove(os.path.join("uploads", f))


    def test_form_can_update_image(self):
        john = mixer.blend(User, id=123, email="john@gmail.com")
        f = SimpleUploadedFile("file.jpg", b"\xff\xd8\xff\xdb\x00C\x00\x03\x02\x02\x02\x02\x02\x03\x02\x02\x02\x03\x03\x03\x03\x04\x06\x04\x04\x04\x04\x04\x08\x06\x06\x05\x06\t\x08\n\n\t\x08\t\t\n\x0c\x0f\x0c\n\x0b\x0e\x0b\t\t\r\x11\r\x0e\x0f\x10\x10\x11\x10\n\x0c\x12\x13\x12\x10\x13\x0f\x10\x10\x10\xff\xc9\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xcc\x00\x06\x00\x10\x10\x05\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf \xff\xd9")
        form = UpdateUserImageForm({"image": f}, files={"image": f}, instance=john)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(john.image.name, "123bVXNlcg.jpg")
    

    def test_can_remove_image(self):
        john = mixer.blend(User, image=SimpleUploadedFile("file.png", b"\x00\x01"))
        form = UpdateUserImageForm({"image": ""}, files={"image": ""}, instance=john)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(john.image.name, "")