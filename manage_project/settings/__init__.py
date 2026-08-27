"""
This package is not a usable Django settings module.

Set DJANGO_SETTINGS_MODULE explicitly to one of:
  - manage_project.settings.dev
  - manage_project.settings.prod

The previous `from .dev import *` fallback has been removed so production
settings can never be silently skipped.
"""
import os

_module = os.environ.get('DJANGO_SETTINGS_MODULE', '')
if _module in ('', 'manage_project.settings'):
    raise ImportError(
        "DJANGO_SETTINGS_MODULE must be set explicitly to "
        "'manage_project.settings.dev' or 'manage_project.settings.prod'. "
        "The package manage_project.settings no longer auto-imports development settings."
    )
