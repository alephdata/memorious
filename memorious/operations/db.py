import datetime

from memorious.core import datastore


def db(context, data):
    """Insert or update `data` as a row into specified db table"""
    table = datastore[context.params.get("table")]
    unique_keys = context.params.get("unique", [])
    now = datetime.datetime.now()
    data["__last_seen"] = now
    if unique_keys:
        updated = table.update(data, unique_keys, return_count=True)
        if updated:
            return
    data["__first_seen"] = now
    table.insert(data)
