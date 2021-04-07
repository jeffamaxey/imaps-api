import requests
from django.core import mail
from core.models import *
from .base import FunctionalTest

class SignupApiTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        self.user = User.objects.create(
            username="adam", email="adam@crick.ac.uk", name="Adam A",
            last_login=1617712117, created=1607712117, company="The Crick",
            department="MolBio", lab="The Smith Lab", job_title="Researcher",
            phone_number="+441234567890"
        )
    


class SignupTests(SignupApiTests):

    def test_can_signup(self):
        users_at_start = User.objects.count()

        # Create user
        result = self.client.execute("""mutation { signup(
            email: "kate@gmail.com", password: "sw0rdfish123",
            username: "kate", name: "Kate Austen"
        ) { accessToken user { username email name } } }""")

        # An email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["kate@gmail.com"])
        self.assertEqual(mail.outbox[0].subject, "Welcome to iMaps")

        # There's a new user
        self.assertEqual(result["data"]["signup"]["user"], {
            "username": "kate", "email": "kate@gmail.com", "name": "Kate Austen"
        })
        self.assertEqual(User.objects.count(), users_at_start + 1)
        new_user = User.objects.last()
        self.assertEqual(new_user.username, "kate")
        self.assertEqual(new_user.email, "kate@gmail.com")
        self.assertEqual(new_user.name, "Kate Austen")
        self.assertNotEqual(new_user.password, "sw0rdfish123")
        self.assertLess(abs(time.time() - new_user.last_login), 3)
        self.assertLess(abs(time.time() - new_user.created), 3)

        # An access token has been returned
        access_token = result["data"]["signup"]["accessToken"]
        algorithm, payload, secret = access_token.split(".")
        payload = json.loads(base64.b64decode(payload + "==="))
        self.assertEqual(payload["sub"], new_user.id)
        self.assertLess(time.time() - payload["iat"], 10)
        self.assertLess(time.time() - payload["expires"] - 900, 10)

        # A HTTP-only cookie has been set with the refresh token
        cookie = self.client.session.cookies._cookies["localhost.local"]["/"]["refresh_token"]
        self.assertIn("HttpOnly", cookie._rest)
        self.assertLess(abs(time.time() + 31536000 - cookie.expires), 10)
        refresh_token = cookie.value
        algorithm, payload, secret = access_token.split(".")
        payload = json.loads(base64.b64decode(payload + "==="))
        self.assertEqual(payload["sub"], new_user.id)
        self.assertLess(time.time() - payload["iat"], 10)
        self.assertLess(time.time() - payload["expires"] - 31536000, 10)
    

    def test_signup_validation(self):
        users_at_start = User.objects.count()

        # Name must be short enough
        self.check_query_error("""mutation { signup(
            email: "kate@gmail.com", password: "sw0rdfish123",
            username: "kate",
            name: "000001111122222333334444455555666667777788888999990"
        ) { accessToken } }""", message="50 characters")
        self.assertEqual(User.objects.count(), users_at_start)
        self.assertEqual(len(mail.outbox), 0)

        # Email must be unique
        self.check_query_error("""mutation { signup(
            email: "adam@crick.ac.uk", password: "sw0rdfish123",
            username: "kate", name: "Kate Austen"
        ) { accessToken } }""", message="already exists")
        self.assertEqual(User.objects.count(), users_at_start)
        self.assertFalse("refresh_token" in self.client.session.cookies)
        self.assertEqual(len(mail.outbox), 0)

        # Username must be unique
        self.check_query_error("""mutation { signup(
            email: "kate@gmail.com", password: "sw0rdfish123",
            username: "adam", name: "Kate Austen"
        ) { accessToken } }""", message="already exists")
        self.assertEqual(User.objects.count(), users_at_start)
        self.assertFalse("refresh_token" in self.client.session.cookies)
        self.assertEqual(len(mail.outbox), 0)

        # Username must be short enough
        self.check_query_error("""mutation { signup(
            email: "kate@gmail.com", password: "sw0rdfish123",
            name: "Kate Austen",
            username: "0001112223334445556667778889990"
        ) { accessToken } }""", message="30 characters")
        self.assertEqual(User.objects.count(), users_at_start)
        self.assertFalse("refresh_token" in self.client.session.cookies)
        self.assertEqual(len(mail.outbox), 0)

        # Username must be long enough
        self.check_query_error("""mutation { signup(
            email: "kate@gmail.com", password: "sw0rdfish123",
            name: "Kate Austen",
            username: "1"
        ) { accessToken } }""", message="2 characters")
        self.assertEqual(User.objects.count(), users_at_start)
        self.assertFalse("refresh_token" in self.client.session.cookies)
        self.assertEqual(len(mail.outbox), 0)

        # Password must be 9 or more characters
        self.check_query_error("""mutation { signup(
            email: "kate@gmail.com", password: "sw0rd123",
            username: "kate", name: "Kate Austen"
        ) { accessToken } }""", message="too short")
        self.assertEqual(User.objects.count(), users_at_start)
        self.assertFalse("refresh_token" in self.client.session.cookies)
        self.assertEqual(len(mail.outbox), 0)

        # Password can't be numeric
        self.check_query_error("""mutation { signup(
            email: "kate@gmail.com", password: "238442378572385238",
            username: "kate", name: "Kate Austen"
        ) { accessToken } }""", message="numeric")
        self.assertEqual(User.objects.count(), users_at_start)
        self.assertFalse("refresh_token" in self.client.session.cookies)
        self.assertEqual(len(mail.outbox), 0)

        # Password must be reasonably uncommon
        self.check_query_error("""mutation { signup(
            email: "kate@gmail.com", password: "password123",
            username: "kate", name: "Kate Austen"
        ) { accessToken } }""", message="too common")
        self.assertEqual(User.objects.count(), users_at_start)
        self.assertFalse("refresh_token" in self.client.session.cookies)
        self.assertEqual(len(mail.outbox), 0)