import os
from uuid import uuid4
from normality import stringify


def make_key(*criteria):
    """Make a string key out of many criteria."""
    criteria = [stringify(c) for c in criteria]
    criteria = [c for c in criteria if c is not None]
    if len(criteria):
        return ':'.join(criteria)


def random_filename(path=None):
    """Make a UUID-based file name which is extremely unlikely
    to exist already."""
    filename = uuid4().hex
    if path is not None:
        filename = os.path.join(path, filename)
    return filename
