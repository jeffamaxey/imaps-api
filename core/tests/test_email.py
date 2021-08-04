from mixer.backend.django import mixer
from django.test import TestCase
from django.core import mail
from core.models import User
from core.email import *

class WelcomeEmailTests(TestCase):

    def test_can_send_welcome_email(self):
        self.assertEqual(len(mail.outbox), 0)
        user = mixer.blend(User, name="John", email="john@gmail.com", username="jlocke")
        send_welcome_email(user, "site.com")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["john@gmail.com"])
        self.assertIn("Dear John", mail.outbox[0].body)
        self.assertIn("jlocke", mail.outbox[0].body)
        self.assertIn("href=\"site.com\"", mail.outbox[0].body)



class ResetEmailTests(TestCase):

    def test_can_send_reset_email(self):
        self.assertEqual(len(mail.outbox), 0)
        user = mixer.blend(User, name="John", email="john@gmail.com")
        send_reset_email(user, "site.com?token")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["john@gmail.com"])
        self.assertIn("Dear John", mail.outbox[0].body)
        self.assertIn("href=\"site.com?token\"", mail.outbox[0].body)
    

    def test_can_send_reset_warning_email(self):
        self.assertEqual(len(mail.outbox), 0)
        send_reset_warning_email("john@gmail.com")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["john@gmail.com"])
        self.assertIn("Dear john@gmail.com", mail.outbox[0].body)
        self.assertNotIn("token", mail.outbox[0].body)