import os
from contextlib import redirect_stderr
import kirjava
from datetime import datetime
from unittest.mock import Mock, patch
from django.test.utils import override_settings
from django.test import LiveServerTestCase
from core.models import User

@override_settings(STATIC_URL="/static/")
class FunctionalTest(LiveServerTestCase):

    def setUp(self):
        self.client = kirjava.Client(self.live_server_url + "/graphql")
        self.client.headers["Accept"] = "application/json"
        self.client.headers["Content-Type"] = "application/json"
        self.files_at_start = os.listdir("uploads")
        self.user = User.objects.create(
            id=1, username="adam", email="adam@crick.ac.uk", name="Adam A",
            last_login=1617712117, created=1607712117
        )
        self.client.headers["Authorization"] = f"Bearer {self.user.make_jwt(900)}"
        self.user.set_password("livetogetha")
    

    def tearDown(self):
        for f in os.listdir("uploads"):
            if f not in self.files_at_start:
                if os.path.exists(os.path.join("uploads", f)):
                    os.remove(os.path.join("uploads", f))
    

    def check_query_error(self, query, message="does not exist"):
        """Sends a query and asserts that the server report the object doesn't
        exist."""

        with open(os.devnull, "w") as fnull:
            with redirect_stderr(fnull) as err:
                result = self.client.execute(query)
                self.assertIn(message, result["errors"][0]["message"])



class TokenFunctionaltest(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        self.client.headers["Authorization"] = f"Bearer {self.user.make_access_jwt()}"