from unittest.mock import patch, Mock, PropertyMock, MagicMock
from mixer.backend.django import mixer
from django.test import TestCase
from django.conf import settings
from core.middleware import *

class AuthMiddlewareTests(TestCase):

    def setUp(self):
        self.request = Mock(path="/", refresh_token=None)
        self.response = Mock()
        self.callback = MagicMock()
        self.callback.return_value = self.response
        self.mw = AuthenticationMiddleware(self.callback)
        self.user = mixer.blend(User, username="john")
    

    @patch("core.middleware.User.from_token")
    def test_middleware_assigns_from_output_to_request(self, mock_from):
        self.request.META = {"HTTP_AUTHORIZATION": "Bearer 12345"}
        response = self.mw(self.request)
        mock_from.assert_called_with("12345")
        self.assertEqual(self.request.user, mock_from.return_value)
    

    @patch("core.middleware.User.from_token")
    def test_middleware_does_nothing_if_no_refresh_token_flag(self, mock_from):
        response = self.mw(self.request)
        self.assertFalse(self.response.set_cookie.called)
        self.assertFalse(self.response.delete_cookie.called)
    

    @patch("core.middleware.User.from_token")
    def test_middleware_deletes_refresh_token_if_false_flag(self, mock_from):
        self.request.refresh_token = False
        response = self.mw(self.request)
        self.assertFalse(self.response.set_cookie.called)
        self.response.delete_cookie.assert_called_with("refresh_token")
    

    @patch("core.middleware.User.from_token")
    def test_middleware_can_set_cookie(self, mock_from):
        self.request.refresh_token = "ABCDEFGH"
        response = self.mw(self.request)
        self.assertFalse(self.response.delete_cookie.called)
        self.response.set_cookie.assert_called_with(
            "refresh_token", value="ABCDEFGH", httponly=True, max_age=31536000
        )