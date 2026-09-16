from django import template

try:
    from core.dates import format_bs, format_bs_short
except Exception:  # pragma: no cover - degrade to showing the stored value
    def format_bs(value):
        return '' if value is None or value == '' else str(value)

    def format_bs_short(value):
        return '' if value is None or value == '' else str(value)

register = template.Library()


@register.filter
def to_bs(value):
    """Format a stored A.D. date/datetime as Bikram Sambat: भदौ ३१, २०८३."""
    return format_bs(value)


@register.filter
def to_bs_short(value):
    """Format a stored B.S. date compactly: २०८३-०५-३१."""
    return format_bs_short(value)


# Alias so any template can use the compact form as |bs
@register.filter(name='bs')
def bs(value):
    return format_bs_short(value)
