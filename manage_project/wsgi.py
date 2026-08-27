"""
WSGI config for manage_project.

Defaults to production settings. Override with DJANGO_SETTINGS_MODULE
when you intentionally want a different environment.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manage_project.settings.prod')
application = get_wsgi_application()