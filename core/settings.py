import environ

ALLOWED_HOSTS = []

env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, "12345"),
    DB_ENGINE=(str, "django.db.backends.sqlite3"),
    DB_NAME=(str, "db.sqlite3"),
    DB_HOST=(str, "localhost"),
    DB_USER=(str, ""),
    DB_PASSWORD=(str, ""),
    MEDIA_ROOT=(str, "uploads"),
    DATA_ROOT=(str, "data"),
    PEKA_ROOT=(str, "peka/data"),
    ADMIN=(bool, False),
    MAILGUN_API_KEY=(str, "MAILGUN_KEY"),
    EMAIL_HOST_PASSWORD=(str, "EMAIL_HOST_PASSWORD"),
    SERVE_FILES=(bool, False)
)

ALLOWED_HOSTS = ["*"]

DEBUG = env("DEBUG")

SECRET_KEY = env("SECRET_KEY")

ROOT_URLCONF = "core.urls"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "graphene_django",
    "corsheaders",
    "core",
    "peka",
    "django_cleanup.apps.CleanupConfig",
]

USE_TZ = True
TIME_ZONE = "UTC"

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "core.middleware.AuthenticationMiddleware"
]

DATABASES = {"default": {
    "ENGINE": env("DB_ENGINE"),
    "NAME": env("DB_NAME"),
    "USER": env("DB_USER"),
    "HOST": env("DB_HOST"),
    "PASSWORD": env("DB_PASSWORD"),
}}

AUTH_PASSWORD_VALIDATORS = [{
    "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    "OPTIONS": {"min_length": 9}
},{
    "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
}, {
    "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
}]

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

TOKEN_TIMEOUT = 15
SESSION_LENGTH_DAYS = 365

GRAPHENE = {"SCHEMA": "core.schema.schema"}

SERVE_FILES = env("SERVE_FILES")
MEDIA_URL = "/uploads/"
MEDIA_ROOT = env("MEDIA_ROOT")
DATA_ROOT = env("DATA_ROOT")
PEKA_ROOT = env("PEKA_ROOT")

EMAIL_HOST = "smtp.eu.mailgun.org"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "postmaster@imaps.goodwright.org"
MAILGUN_API_KEY = env("MAILGUN_API_KEY")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")