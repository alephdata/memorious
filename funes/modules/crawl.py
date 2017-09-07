from funes.operation import operation
from funes.modules.extras.rule import Rule


@operation()
def crawl(context, data):
    url = data.get('url')
    crawl_path = data.get('crawl_path', [])
    if url in crawl_path:
        context.log.info('[Skip]: %r', url)
        return

    res = context.request(url)
    if res is None:
        return

    rules = context.params.get('rules', {'match_all': {}})
    if not Rule.get_rule(rules).apply(res):
        context.log.info('[Crawl rule skip]: %r', res.url)
        return

    data['crawl_path'] = crawl_path + [res.url]
    if res.url in crawl_path:
        context.log.info('[Skip]: %r', url)
        return
    context.log.info("[Crawling]: %r", res.url)

    if res.status_code > 300:
        context.log.warning("[Failure]: %r, [status]: %r", res.url,
                            res.status_code)
        return

    data['res'] = res
    context.emit(data=data)
