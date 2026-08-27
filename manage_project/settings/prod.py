"""
Production settings for manage_project.
"""
from django.core.exceptions import ImproperlyConfigured

from .base import *

# Production is never debug, regardless of a leftover .env value.
DEBUG = False

ALLOWED_HOSTS = env('ALLOWED_HOSTS')
if not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        'ALLOWED_HOSTS must be a list of real hostnames in production '
        '(do not use "*"). Example: dancestudio.onrender.com'
    )

CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS')

if (
    not SECRET_KEY
    or 'insecure' in SECRET_KEY.lower()
    or SECRET_KEY in {'replace-this-in-production', 'django-insecure-dev-do-not-use-in-production'}
):
    raise ImproperlyConfigured(
        'DJANGO_SECRET_KEY must be a unique, random value in production. '
        'Generate one with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" '
        'Never reuse the placeholder from .env.example.'
    )

# TLS / cookies (behind Render/Railway/PythonAnywhere TLS termination)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# HSTS and related headers
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'

# Compressed static files served by WhiteNoise (non-strict to prevent missing manifest 500 crashes)
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}
WHITENOISE_MANIFEST_STRICT = False

# Email
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')

# Remove debug toolbar if a local overlay added it
if 'debug_toolbar' in INSTALLED_APPS:
    INSTALLED_APPS.remove('debug_toolbar')
if 'debug_toolbar.middleware.DebugToolbarMiddleware' in MIDDLEWARE:
    MIDDLEWARE.remove('debug_toolbar.middleware.DebugToolbarMiddleware')