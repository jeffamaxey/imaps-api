import re
import json
import time
import base64
from django.core import mail
from core.models import User
from .base import FunctionalTest

class LoginTests(FunctionalTest):

    def test_can_login(self):
        # Send credentials
        result = self.client.execute("""mutation { login(
            username: "adam", password: "livetogetha",
        ) { accessToken user { username email name } } }""")

        # User is returned
        self.assertEqual(result["data"]["login"]["user"], {
            "username": "adam", "email": "adam@crick.ac.uk", "name": "Adam A"
        })

        # An access token has been returned
        access_token = result["data"]["login"]["accessToken"]
        payload = access_token.split(".")[1]
        payload = json.loads(base64.b64decode(payload + "==="))
        self.assertEqual(payload["sub"], self.user.id)
        self.assertLess(time.time() - payload["iat"], 10)
        self.assertLess(time.time() - payload["expires"] - 900, 10)

        # A HTTP-only cookie has been set with the refresh token
        cookie = self.client.session.cookies._cookies["localhost.local"]["/"]["imaps_refresh_token"]
        self.assertIn("HttpOnly", cookie._rest)
        self.assertLess(abs(time.time() + 31536000 - cookie.expires), 10)
        imaps_refresh_token = cookie.value
        payload = imaps_refresh_token.split(".")[1]
        payload = json.loads(base64.b64decode(payload + "==="))
        self.assertEqual(payload["sub"], self.user.id)
        self.assertLess(time.time() - payload["iat"], 10)
        self.assertLess(time.time() - payload["expires"] - 31536000, 10)

        # Last login has been updated
        self.user.refresh_from_db()
        self.assertLess(time.time() - self.user.last_login, 10)
    

    def test_login_can_fail(self):
        # Incorrect username
        self.check_query_error("""mutation { login(
            username: "claire", password: "livetogetha"
        ) { accessToken} }""", message="Invalid credentials")
        self.assertFalse("imaps_refresh_token" in self.client.session.cookies)
        self.user.refresh_from_db()
        self.assertEqual(self.user.last_login, 1617712117)

        # Incorrect password
        self.check_query_error("""mutation { login(
            username: "adam", password: "wrongpassword"
        ) { accessToken} }""", message="Invalid credentials")
        self.assertFalse("imaps_refresh_token" in self.client.session.cookies)
        self.user.refresh_from_db()
        self.assertEqual(self.user.last_login, 1617712117)



class PasswordResetRequestTests(FunctionalTest):

    def test_can_request_password_reset(self):
        # Request a password reset
        result = self.client.execute("""mutation { requestPasswordReset(
            email: "adam@crick.ac.uk"
        ) { success } }""")
        
        # Server reports success
        self.assertTrue(result["data"]["requestPasswordReset"]["success"])

        # An email was sent with a link
        self.assertEqual(len(mail.outbox), 1)
        token = re.findall(r"token=([a-zA-Z0-9]+)", mail.outbox[0].body)[0]
        self.assertEqual(len(token), 128)

        # The user has been updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.password_reset_token, token)
    

    def test_password_reset_request_failure(self):
        # Invalid email
        result = self.client.execute("""mutation { requestPasswordReset(
            email: "wrong@gmail.com"
        ) { success } }""")
        self.assertTrue(result["data"]["requestPasswordReset"]["success"])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("associated", mail.outbox[0].body)