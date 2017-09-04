from funes.operation import operation


@operation()
def webcrawler(context, data):
    if context.params.get('retain_rules') is None:
        context.params['retain_rules'] = {'match_all': {}}
    if context.params.get('crawl_rules') is None:
        context.params['crawl_rules'] = {'match_all': {}}
    data = {}
    if context.params.get('seed_url') is not None:
        data['url'] = context.params.get('seed_url')
    context.params['count'] = 0
    context.emit(data=data)
