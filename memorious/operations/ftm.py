from memorious.model import Cache


def cache_ftm_entity(context, data):
    Cache.cache_entity(context.crawler, data)
