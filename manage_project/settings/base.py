"""
Django settings for manage_project.

This file is the base settings shared by all environments.
Sensitive values are loaded from environment variables.
"""
import os
from datetime import timedelta
from pathlib import Path
import environ as django_environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Environment configuration
env = django_environ.Env(
    DJANGO_SECRET_KEY=(str, 'django-insecure-dev-do-not-use-in-production'),
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    DATABASE_URL=(str, f'sqlite:///{(BASE_DIR / "db.sqlite3").as_posix()}'),
    # Security
    CSRF_TRUSTED_ORIGINS=(list, []),
    # Email (for password reset)
    EMAIL_BACKEND=(str, 'django.core.mail.backends.console.EmailBackend'),
    EMAIL_HOST=(str, ''),
    EMAIL_PORT=(int, 587),
    EMAIL_USE_TLS=(bool, False),
    EMAIL_HOST_USER=(str, ''),
    EMAIL_HOST_PASSWORD=(str, ''),
    # Studio branding
    STUDIO_NAME=(str, 'Dance Studio'),
    STUDIO_LOGO_URL=(str, ''),
    CURRENCY_SYMBOL=(str, 'रु'),
    CURRENCY_DECIMALS=(int, 2),
)

env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY
SECRET_KEY = env('DJANGO_SECRET_KEY')
DEBUG = env('DEBUG', default=True)
ALLOWED_HOSTS = env('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost', '*'])

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'axes',
    'crispy_forms',
    'crispy_tailwind',
]

LOCAL_APPS = [
    'accounts',
    'core',
    'students',
    'teachers',
    'packages',
    'styles',
    'billing',
    'dashboard',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.audit.AuditMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'manage_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.studio_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'manage_project.wsgi.application'

# Database: SQLite by default (free-tier / storage-lean). Override with DATABASE_URL.
DATABASES = {
    'default': env.db('DATABASE_URL', default=f'sqlite:///{(BASE_DIR / "db.sqlite3").as_posix()}')
}

# Password validators — Django's standard four
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# django-axes: 5 failed attempts, 15-minute cooloff
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address']
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_CALLABLE = None
AXES_COOLOFF_MESSAGE = (
    'Account locked: too many login attempts. Please try again in 15 minutes.'
)

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/
LANGUAGE_CODE = 'en-NP'  # Nepal locale, will confirm with client
TIME_ZONE = 'Asia/Kathmandu'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# User-uploaded files (invoice PDFs, photos). Never commit this directory.
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'tailwind'
CRISPY_TEMPLATE_PACK = 'tailwind/inline'

# Admin configuration
ADMIN_SITE_HEADER = env('STUDIO_NAME')
ADMIN_SITE_TITLE = 'Studio Administration'
ADMIN_INDEX_TITLE = 'Dance Studio Management System'

# Studio branding (accessible in templates via context processor)
STUDIO_NAME = env('STUDIO_NAME')
STUDIO_LOGO_URL = env('STUDIO_LOGO_URL')
CURRENCY_SYMBOL = env('CURRENCY_SYMBOL')
CURRENCY_DECIMALS = env('CURRENCY_DECIMALS')

# Authentication
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
AUTH_USER_MODEL = 'auth.User'
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Session timeout (12 hours idle)
SESSION_COOKIE_AGE = 12 * 60 * 60
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Security headers
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True