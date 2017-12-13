import re
import dateparser
from datetime import datetime


def parse_date(text, format_hint=None):
    if format_hint is not None:
        return datetime.strptime(text, format_hint)
    else:
        return dateparser.parse(text)


def iso_date(text, format_hint=None):
    return parse_date(text, format_hint).isoformat()
