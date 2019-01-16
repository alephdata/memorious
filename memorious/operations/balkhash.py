import json

import balkhash


def balkhash_emit(context, data):
    dataset = get_dataset(context)
    dataset.put(data["id"], data)


def get_dataset(context):
    if hasattr(context.stage, '_balkhash_dataset'):
        return context.stage._balkhash_dataset
    remote = bool(context.params.get("remote")) or False
    storage = balkhash.init(remote=remote)
    name = context.params.get("dataset_name") or context.crawler.name
    dataset = storage.create_dataset(name=name)
    context.stage._balkhash_dataset = dataset
    return dataset
