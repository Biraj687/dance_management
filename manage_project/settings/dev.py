"""
Development settings for manage_project.
"""
from .base import *

# Override for development
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', 'testserver']

# CSRF trusted origins for development
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# Disable security redirects in dev
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Email to console in dev
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'