from mixer.backend.django import mixer
from django.test import TestCase
from django.db.utils import IntegrityError
from django.db import transaction
from core.models import User

class UserCreationTests(TestCase):

    def test_can_create_user(self):
        user = User.objects.create(
            username="locke", email="john@gmail.com", name="John Locke",
        )
        self.assertIsNone(user.last_login)
        self.assertEqual(str(user), "John Locke (locke)")
        self.assertEqual(user.password, "")
        self.assertFalse(user.groups.count())
        self.assertFalse(user.admin_groups.count())
        self.assertNotEqual(user.id, 1)
    

    def test_user_uniqueness(self):
        user = mixer.blend(User, username="locke", email="john@gmail.com")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create(username="locke2", email="john@gmail.com")
        self.assertEqual(User.objects.count(), 1)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create(username="locke", email="john2@gmail.com")
        self.assertEqual(User.objects.count(), 1)



class UserPasswordTests(TestCase):

    def test_can_set_password(self):
        user = User.objects.create(
            username="locke", email="john@gmail.com", name="John Locke",
        )
        self.assertEqual(user.password, "")
        user.set_password("sw0rdfish123")
        self.assertNotEqual(user.password, "sw0rdfish")
        algorithm, iterations, salt, hash_ = user.password.split("$")
        self.assertGreaterEqual(int(iterations), 100000)
        