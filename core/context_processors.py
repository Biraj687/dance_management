"""
Context processors for adding studio settings to all templates.
"""
from django.conf import settings


def studio_settings(request):
    """
    Add studio branding and currency settings to template context.
    """
    return {
        'studio_name': getattr(settings, 'STUDIO_NAME', 'Dance Studio'),
        'studio_logo_url': getattr(settings, 'STUDIO_LOGO_URL', ''),
        'currency_symbol': getattr(settings, 'CURRENCY_SYMBOL', 'रु'),
        'currency_decimals': getattr(settings, 'CURRENCY_DECIMALS', 2),
    }
