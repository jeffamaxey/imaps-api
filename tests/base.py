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
        "users.json"
    ]

    def setUp(self):
        self.client = kirjava.Client(self.live_server_url + "/graphql")
        self.client.headers["Accept"] = "application/json"
        self.client.headers["Content-Type"] = "application/json"
    

    def check_query_error(self, query, message="does not exist"):
        """Sends a query and asserts that the server report the object doesn't
        exist."""

        with open(os.devnull, "w") as fnull:
            with redirect_stderr(fnull) as err:
                result = self.client.execute(query)
                self.assertIn(message, result["errors"][0]["message"])