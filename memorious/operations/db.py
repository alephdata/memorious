import datetime
from banal import ensure_list

from memorious.core import datastore


def _recursive_upsert(context, params, data):
    """Insert or update nested dicts recursively"""
    table = params.get("table")
    table = datastore.get_table(table, primary_id=False)
    unique_keys = ensure_list(params.get("unique"))

    children = params.get("children", {})
    nested_calls = []
    for child_params in children:
        key = child_params.get("key")
        child_data_list = data.pop(key, [])
        if isinstance(child_data_list, dict):
            child_data_list = [child_data_list]
        if not (isinstance(child_data_list, list) and
                all(isinstance(i, dict) for i in child_data_list)):
            context.log.warn(
                "Expecting a dict or a lost of dicts as children for key", key
            )
            continue
        if child_data_list:
            table_suffix = child_params.get("table_suffix", key)
            child_params["table"] = params.get("table") + "_" + table_suffix
            parent_id = data.get(child_params.get("parent_id"))
            for child_data in child_data_list:
                child_data["__parent_id"] = parent_id
                nested_calls.append((child_params, child_data))

    data["__last_seen"] = datetime.datetime.utcnow()
    if len(unique_keys):
        updated = table.update(data, unique_keys, return_count=True)
        if updated:
            for child_params, child_data in nested_calls:
                _recursive_upsert(context, child_params, child_data)
            return
    data["__first_seen"] = data["__last_seen"]
    table.insert(data)
    for child_params, child_data in nested_calls:
        _recursive_upsert(context, child_params, child_data)


def db(context, data):
    """Insert or update `data` as a row into specified db table"""
    table = context.params.get("table", context.crawler.name)
    params = context.params
    params["table"] = table
    _recursive_upsert(context, params, data)
