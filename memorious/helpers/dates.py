import pytz
import dateparser
from datetime import datetime


def parse_date(text, format_hint=None):
    if text is None:
        return
    if format_hint is not None:
        parsed = datetime.strptime(text, format_hint)
    else:
        # Strip things that don't belong in dates but websites like to wrap
        # their dates with them anyway
        cleaned = str(text).strip('[] ')
        parsed = dateparser.parse(cleaned)
    return naive_datetime(parsed)


def iso_date(text, format_hint=None):
    parsed = parse_date(text, format_hint)
    if parsed is not None:
        return parsed.isoformat()


def naive_datetime(dt):
    if not isinstance(dt, datetime):
        return dt
    if dt.tzinfo is not None:
        dt = dt.astimezone(pytz.utc)
        dt = dt.replace(tzinfo=None)
    return dt
