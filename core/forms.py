"""
Form fields and widgets that let staff enter Bikram Sambat (B.S.) dates while
the database keeps storing Gregorian (A.D.) dates.
"""
from datetime import date, datetime

from django import forms

from core.dates import BS_YEAR_MAX, BS_YEAR_MIN, parse_bs, to_bs_input


class BSDateInput(forms.TextInput):
    """Text input that shows a B.S. date, e.g. 2083-05-31."""

    def __init__(self, attrs=None):
        default_attrs = {
            'data-bs-date': 'true',
            'placeholder': 'YYYY-MM-DD (B.S.)',
            'autocomplete': 'off',
            'inputmode': 'numeric',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)


class BSDateField(forms.DateField):
    """
    A date field that accepts a B.S. date from the user and validates it,
    returning the equivalent Gregorian ``datetime.date`` for storage.
    """

    widget = BSDateInput

    default_error_messages = {
        'invalid': 'Enter a valid Bikram Sambat date in YYYY-MM-DD format (B.S.).',
    }

    def __init__(self, *args, min_bs_year=BS_YEAR_MIN, max_bs_year=BS_YEAR_MAX, **kwargs):
        self.min_bs_year = min_bs_year
        self.max_bs_year = max_bs_year
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if value in self.empty_values:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        try:
            return parse_bs(value, self.min_bs_year, self.max_bs_year)
        except (TypeError, ValueError):
            raise forms.ValidationError(self.error_messages['invalid'], code='invalid')

    def prepare_value(self, value):
        if isinstance(value, datetime):
            value = value.date()
        if isinstance(value, date):
            return to_bs_input(value)
        return value
