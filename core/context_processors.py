"""
Context processors for adding studio settings to all templates.
"""
from django.conf import settings

try:
    from core.dates import today_bs_formatted
except Exception:  # pragma: no cover - the site keeps working if BS support is unavailable
    today_bs_formatted = None


def studio_settings(request):
    """
    Add studio branding, currency, and today's date in Bikram Sambat (B.S.).
    """
    return {
        'studio_name': getattr(settings, 'STUDIO_NAME', 'Dance Studio'),
        'studio_logo_url': getattr(settings, 'STUDIO_LOGO_URL', ''),
        'currency_symbol': getattr(settings, 'CURRENCY_SYMBOL', 'रु'),
        'currency_decimals': getattr(settings, 'CURRENCY_DECIMALS', 2),
        'today_bs': today_bs_formatted() if today_bs_formatted else '',
    }
