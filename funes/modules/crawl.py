from funes.operation import operation
from funes.modules.extras.rule import Rule


@operation()
def crawl(context, data):
    url = data.get('url')
    if context.skip_incremental(url):
        context.log.info('[Skip incremental]: %r', url)
        return

    res = context.request(url)
    if res is None:
        return

    crawl_rules = context.params.get('crawl_rules', {'match_all': {}})
    if not Rule.get_rule(crawl_rules).apply(res):
        context.log.info('[Crawl rule skip]: %r', res.url)
        return

    data['path'] = data.get('path', []) + [res.url]
    context.log.info("[Crawling]: %r", res.url)

    if res is None:
        return
    if res.status_code > 300:
        context.log.warning("[Failure]: %r, [status]: %r", res.url,
                            res.status_code)
        return

    data['res'] = res
    retain_rules = context.params.get('retain_rules', {'match_all': {}})
    if Rule.get_rule(retain_rules).apply(res):
        context.emit(rule='retain', data=data)

    if 'html' in res.content_type and not _terminate_path(data):
        context.emit(data=data)


def _terminate_path(data):
    depth = data.get('depth')
    path = data.get('path')
    if depth is None or depth < 0:
        return False
    return len(path) >= depth
