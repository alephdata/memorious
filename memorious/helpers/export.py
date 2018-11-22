from memorious.model import Cache
import json


def export_entities(crawler, params):
    entities = Cache.export_entities(crawler)
    # TODO: Export to s3
    with open("{}.json".format(crawler.name), "w") as fp:
        json.dump(entities, fp, indent=4)
