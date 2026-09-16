"""
Bikram Sambat (BS) date helpers for this Nepali studio site.

Storage stays Gregorian (AD) in the database. Every user-facing date is
converted to BS. ReportLab PDFs use ASCII BS (Helvetica has no Devanagari).
"""
import re
from datetime import date, datetime

import nepali_datetime
from django.utils import timezone as django_timezone

NEPALI_LONG = '%N %D, %K'  # Bhadra 27, 2083
BS_ISO = '%Y-%m-%d'        # 2083-05-27
# ASCII compact form: every user-facing date must render as 2083-05-27, not
# the Devanagari २०८३-०५-२७. Kept as an alias so existing callers keep working.
NEPALI_SHORT = BS_ISO

# Sensible bounds for BS dates entered by staff. This stops an accidental
# Gregorian year such as "2026" from silently being read as BS 2026 (~AD 1970).
BS_YEAR_MIN = 2070
BS_YEAR_MAX = 2110

_DEVANAGARI_DIGITS = str.maketrans('०१२३४५६७८९', '0123456789')
_BS_DATE_RE = re.compile(r'^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$')


def _to_local(value):
    """Convert an aware datetime to the project timezone (Asia/Kathmandu)."""
    if isinstance(value, datetime) and django_timezone.is_aware(value):
        try:
            return django_timezone.localtime(value)
        except (ValueError, OverflowError):
            return value
    return value


def _as_ad_date(value):
    if value is None or value == '':
        return None
    if isinstance(value, datetime):
        return _to_local(value).date()
    if isinstance(value, date):
        return value
    if isinstance(value, nepali_datetime.date):
        return value.to_datetime_date()
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        # Already a BS string such as date_of_birth_bs — leave as-is by returning
        # None only when it cannot be parsed as AD ISO. Callers handle strings
        # separately.
        try:
            year, month, day = [int(part) for part in text.replace('/', '-').split('-')[:3]]
            return date(year, month, day)
        except (TypeError, ValueError):
            return None
    return None


def to_bs_date(value):
    """Return a nepali_datetime.date, or None."""
    if isinstance(value, nepali_datetime.date):
        return value
    ad_date = _as_ad_date(value)
    if ad_date is None:
        return None
    try:
        return nepali_datetime.date.from_datetime_date(ad_date)
    except Exception:
        return None


def parse_bs(value, min_year=BS_YEAR_MIN, max_year=BS_YEAR_MAX):
    """
    Parse a Bikram Sambat date and return a Gregorian ``datetime.date``.

    Accepts ASCII or Devanagari digits and '-', '/' or '.' separators, e.g.
    ``2083-05-31`` or ``२०८३/०५/३१``. Raises ``ValueError`` for anything that
    is not a valid BS date, including an accidental Gregorian year such as
    ``2026`` (outside the accepted B.S. range).
    """
    if isinstance(value, nepali_datetime.date):
        return value.to_datetime_date()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value is None:
        raise ValueError('Empty B.S. date.')
    text = str(value).strip().translate(_DEVANAGARI_DIGITS)
    if not text:
        raise ValueError('Empty B.S. date.')
    match = _BS_DATE_RE.match(text)
    if not match:
        raise ValueError(f'Invalid B.S. date: {value!r}')
    year, month, day = (int(part) for part in match.groups())
    if min_year is not None and year < min_year:
        raise ValueError(f'B.S. year {year} is out of range (minimum {min_year}).')
    if max_year is not None and year > max_year:
        raise ValueError(f'B.S. year {year} is out of range (maximum {max_year}).')
    return nepali_datetime.date(year, month, day).to_datetime_date()


def format_bs(value, format_string=BS_ISO, with_time=True):
    """
    Format an AD date/datetime as Bikram Sambat.

    Defaults to the ASCII ISO form (``2083-05-31``) so that no code path can
    leak Devanagari digits such as ``२०८१-०३-०५``. Pass ``NEPALI_LONG``
    explicitly if a written-out B.S. month name is ever needed.

    Strings that are already BS (e.g. date_of_birth_bs) are returned unchanged.
    """
    if value is None or value == '':
        return ''
    time_part = ''
    if isinstance(value, datetime):
        value = _to_local(value)
        if with_time:
            time_part = value.strftime(' %H:%M')
        value = value.date()
    if isinstance(value, str):
        return value
    bs_date = to_bs_date(value)
    if bs_date is None:
        return str(value)
    try:
        return bs_date.strftime(format_string) + time_part
    except Exception:
        return str(value)


def format_bs_iso(value):
    """ASCII BS ISO date for PDFs, CSVs, and compact tables: 2083-05-27."""
    return format_bs(value, BS_ISO, with_time=False)


def format_bs_short(value):
    """Compact BS date with ASCII digits: 2083-05-27."""
    return format_bs(value, BS_ISO, with_time=False)


def to_bs_input(value):
    """ASCII BS ISO value for a text input: 2083-05-27."""
    return format_bs(value, BS_ISO, with_time=False)


def today_bs_formatted(format_string=BS_ISO):
    return nepali_datetime.date.today().strftime(format_string)
