import os
from .secrets import *

ALLOWED_HOSTS = []

DEBUG = True

ROOT_URLCONF = "core.urls"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "graphene_django",
    "corsheaders",
    "core",
    "peka",
    "django_cleanup.apps.CleanupConfig",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "core.middleware.AuthenticationMiddleware"
]

AUTH_PASSWORD_VALIDATORS = [{
    "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    "OPTIONS": {"min_length": 9}
},{
    "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
}, {
    "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
}]

STATIC_URL = "/static/"

MEDIA_ROOT = os.path.join(BASE_DIR, "uploads") if DEBUG else\
    os.path.join(BASE_DIR, "..", "..", "static.imaps.goodwright.org")
MEDIA_URL = "/media/"

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

ID_DIGITS_LENGTH = 18

GRAPHENE = {"SCHEMA": "core.schema.schema"}

SESSION_LENGTH_DAYS = 365