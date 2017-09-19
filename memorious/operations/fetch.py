from memorious.helpers.rule import Rule


def fetch(context, data):
    url = data.get('url')
    result = context.http.get(url)

    rules = context.params.get('rules', {'match_all': {}})
    if not Rule.get_rule(rules).apply(result):
        context.log.info('Fetch skip: %r', result.url)
        return

    if not result.ok:
        context.log.warning("Fetch fail [%s]: %s",
                            result.status_code,
                            result.url)
        return

    context.log.info("Fetched [%s]: %r", result.status_code, result.url)
    data.update(result.serialize())
    if url != result.url:
        context.set_run_tag(result.url, None)
    context.emit(data=data)
