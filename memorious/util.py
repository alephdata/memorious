import os
from uuid import uuid4


def random_filename(path=None):
    """Make a UUID-based file name which is extremely unlikely
    to exist already."""
    filename = uuid4().hex
    if path is not None:
        filename = os.path.join(path, filename)
    return filename
