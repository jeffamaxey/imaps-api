from unittest.mock import patch, Mock, PropertyMock, MagicMock
from mixer.backend.django import mixer
from django.test import TestCase
from django.conf import settings
from core.middleware import *

class ApiAuthMiddlewareTests(TestCase):

    def setUp(self):
        self.request = Mock(path="/")
        self.callback = MagicMock()
        self.mw = AuthenticationMiddleware(self.callback)
        self.user = mixer.blend(User, username="john")


    def test_middleware_does_not_set_cookie_if_no_refresh_token_added(self):
        self.request.refresh_token = None
        response = self.mw(self.request)
        self.assertFalse(response.set_cookie.called)
    

    def test_middleware_does_set_cookie_if_refresh_token_added(self):
        self.request.refresh_token = "abc"
        response = self.mw(self.request)
        response.set_cookie.assert_called_with("refresh_token", value="abc", httponly=True)
        