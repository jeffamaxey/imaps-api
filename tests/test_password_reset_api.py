import requests
import time
from django.core import mail
from core.models import *
from .base import FunctionalTest

class PasswordResetApiTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        self.user = User.objects.create(
            username="adam", email="adam@crick.ac.uk", name="Adam A",
            password_reset_token="12345", password_reset_token_expiry=time.time() + 60
        )



class PasswordResetTests(PasswordResetApiTests):

    def test_can_reset_password(self):
        # The token allows the password to be changed
        result = self.client.execute("""mutation { resetPassword(
            password: "newpassword12345" token: "12345"
        ) { success } }""")

        # Server reports success
        self.assertTrue(result["data"]["resetPassword"]["success"])

        # User can log in with new credentials
        result = self.client.execute("""mutation { login(
            username: "adam", password: "newpassword12345",
        ) { user { username email } } }""")
        self.assertEqual(result["data"]["login"]["user"], {
            "username": "adam", "email": "adam@crick.ac.uk",
        })

        # But can't use same token again
        self.check_query_error("""mutation { resetPassword(
            password: "newpassword12345" token: "12345"
        ) { success } }""", "valid")
    

    def test_can_password_reset_can_fail(self):
        # Wrong token sent
        result = self.check_query_error("""mutation { resetPassword(
            password: "newpassword12345" token: "wrongtoken"
        ) { success } }""", "valid")

        # Correct token sent too late
        self.user.password_reset_token_expiry = time.time() - 1
        self.user.save()
        result = self.check_query_error("""mutation { resetPassword(
            password: "newpassword12345" token: "12345"
        ) { success } }""", "expired")

        # Password not valid
        self.user.password_reset_token_expiry = time.time() + 3600
        self.user.save()
        result = self.check_query_error("""mutation { resetPassword(
            password: "password123" token: "12345"
        ) { success } }""", "common")
        result = self.check_query_error("""mutation { resetPassword(
            password: "smog123" token: "12345"
        ) { success } }""", "at least 9 characters")