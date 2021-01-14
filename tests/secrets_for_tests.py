import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = "test-secret-key"

DATABASES = {"default": {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": os.path.join(BASE_DIR, "db.sqlite3")
}}

EMAIL_HOST = "smtp.eu.mailgun.org"
EMAIL_PORT = 587
EMAIL_HOST_USER = "testuser@imaps.goodwright.org"
EMAIL_HOST_PASSWORD = "test-password-123"
EMAIL_USE_TLS = True