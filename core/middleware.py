import jwt
import time
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse
from .models import User

class AuthenticationMiddleware:
    """Incoming requests will be annotated with a User, or None, based on the
    access token provided. Outgoing responses set a HTTP-only refresh token
    cookie if the request has had one added to it at some point, or removed if
    it has been set to False."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    

    def __call__(self, request):
        request.user = User.from_token(
            request.META.get("HTTP_AUTHORIZATION", "").replace("Bearer ", "")
        )

        response = self.get_response(request)

        try:
            imaps_refresh_token = request.imaps_refresh_token
        except AttributeError: imaps_refresh_token = None
        if imaps_refresh_token is False:
            response.delete_cookie("imaps_refresh_token")
        elif imaps_refresh_token:
            response.set_cookie(
                "imaps_refresh_token", value=imaps_refresh_token, httponly=True,
                max_age=settings.SESSION_LENGTH_DAYS * 86400
            )
        return response