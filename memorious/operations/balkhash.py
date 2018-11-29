import json

import balkhash


def balkhash_emit(context, data):
    dataset = get_dataset(context)
    dataset.put(key=data["id"], val=json.dumps(data), context="entities")


def get_dataset(context):
    if hasattr(context.stage, '_balkhash_dataset'):
        return context.stage._balkhash_dataset
    storage = balkhash.init(
        bucket_postfix=context.params.get("bucket_postfix")
    )
    name = context.params.get("dataset_name") or context.crawler.name
    is_public = context.params.get("is_public")
    if is_public is not True:
        is_public = False
    dataset = storage.create_dataset(name=name, public=is_public)
    context.stage._balkhash_dataset = dataset
    return dataset
