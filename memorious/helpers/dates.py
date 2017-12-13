import re
import dateparser
from datetime import datetime


def parse_date(text, format_hint=None):
    if format_hint is not None:
        return datetime.strptime(text, format_hint)
    else:
        # Strip things that don't belong in dates but websites like to wrap
        # their dates with them anyway
        cleaned = text.strip('[] ')
        return dateparser.parse(cleaned)


def iso_date(text, format_hint=None):
    return parse_date(text, format_hint).isoformat()
