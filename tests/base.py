import os
from contextlib import redirect_stderr
import kirjava
from datetime import datetime
from unittest.mock import Mock, patch
from django.test.utils import override_settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from core.models import User

class FunctionalTest(StaticLiveServerTestCase):

    fixtures = [
        "users.json", "collections.json"
    ]

    def setUp(self):
        self.user = User.objects.get(username="jack")
        self.user.set_password("livetogetha")
        self.client = kirjava.Client(self.live_server_url + "/graphql")
        self.client.headers["Accept"] = "application/json"
        self.client.headers["Content-Type"] = "application/json"
        self.files_at_start = os.listdir("uploads")
    

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