from banal import ensure_list
from ftmstore import get_dataset as get_ftmstore_dataset
from ftmstore.settings import DATABASE_URI, DEFAULT_DATABASE_URI

from memorious.settings import DATASTORE_URI
from memorious.operations.aleph import get_api

ORIGIN = "memorious"


def get_dataset(context, origin=ORIGIN):
    name = context.get("dataset", context.crawler.name)
    origin = context.get("dataset", origin)
    # Either use a database URI that has been explicitly set as a
    # backend, or default to the memorious datastore.
    database_uri = DATABASE_URI
    if DATABASE_URI == DEFAULT_DATABASE_URI:
        database_uri = DATASTORE_URI
    return get_ftmstore_dataset(name, database_uri=database_uri, origin=origin)


def ftm_store(context, data):
    """Store an entity or a list of entities to an ftm store."""
    # This is a simplistic implementation of a balkhash memorious operation.
    # It is meant to serve the use of OCCRP where we pipe data into postgresql.
    dataset = get_dataset(context)
    bulk = dataset.bulk()
    entities = ensure_list(data.get("entities", data))
    for entity in entities:
        context.log.debug("Store entity [%(schema)s]: %(id)s", entity)
        bulk.put(entity, entity.pop("fragment", None))
        context.emit(rule="fragment", data=data, optional=True)
    context.emit(data=data, optional=True)
    bulk.flush()


def ftm_load_aleph(context, data):
    """Write each entity from an ftm store to Aleph via the _bulk API."""
    api = get_api(context)
    if api is None:
        return
    foreign_id = context.params.get("foreign_id", context.crawler.name)
    collection = api.load_collection_by_foreign_id(foreign_id, {})
    collection_id = collection.get("id")
    unsafe = context.params.get("unsafe", False)
    entities = get_dataset(context)
    api.write_entities(collection_id, entities, unsafe=unsafe)
