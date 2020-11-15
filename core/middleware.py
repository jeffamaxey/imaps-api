import jwt
import time
from django.conf import settings
from django.http import JsonResponse
from .models import User

class AuthenticationMiddleware:
    """Outgoing responses set a HTTP-only refresh token cookie if the request
    has had one added to it at some point."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    

    def __call__(self, request):
        response = self.get_response(request)

        try:
            refresh_token = request.refresh_token
        except AttributeError: refresh_token = None
        if refresh_token:
            response.set_cookie("refresh_token", value=refresh_token, httponly=True)

        return response