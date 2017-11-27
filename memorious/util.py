from normality import stringify


def make_key(*criteria):
    """Make a string key out of many criteria."""
    criteria = [stringify(c) for c in criteria]
    criteria = [c for c in criteria if c is not None]
    if len(criteria):
        return ':'.join(criteria)
