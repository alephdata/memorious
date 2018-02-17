import datetime
from banal import ensure_list

from memorious.core import datastore


def db(context, data):
    """Insert or update `data` as a row into specified db table"""
    table = context.params.get("table", context.crawler.name)
    table = datastore.get_table(table, primary_id=False)
    unique_keys = ensure_list(context.params.get("unique"))
    # context.log.info("Save: %s %r", table.name, unique_keys)

    data["__last_seen"] = datetime.datetime.utcnow()
    if len(unique_keys):
        updated = table.update(data, unique_keys, return_count=True)
        if updated:
            return
    data["__first_seen"] = data["__last_seen"]
    table.insert(data)
