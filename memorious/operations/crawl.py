from memorious.helpers.rule import Rule
from memorious.util import normalize_url


def crawl(context, data):
    url = normalize_url(data.get('url'))
    if context.check_run_tag(url):
        context.log.info('Skip: %r', url)
        return

    result = context.http.get(url)
    rules = context.params.get('rules', {'match_all': {}})
    if not Rule.get_rule(rules).apply(result):
        context.log.info('Skip: %r', result.url)
        return

    if not result.ok:
        context.log.warning("Failure [%s]: %s", result.status_code, result.url)
        return

    context.log.info("Crawling [%s]: %r", result.status_code, result.url)
    data.update(result.serialize())
    context.set_run_tag(url, None)
    context.set_run_tag(result.url, None)
    context.emit(data=data)
