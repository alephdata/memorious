from urlparse import urljoin
from funes.operation import operation
from funes.modules.extras.rule import Rule

URL_TAGS = [('a', 'href'),
            ('img', 'src'),
            ('link', 'href'),
            ('iframe', 'src')]


def parse_html(context, data, result):
    context.log.info('Parse: %r', result.url)

    title = result.html.findtext('.//title')
    if title is not None:
        data['title'] = title

    urls = set([])
    for tag_name, attr_name in URL_TAGS:
        for tag in result.html.findall('.//%s' % tag_name):
            attr = tag.get(attr_name)
            if attr is None:
                continue
            url = urljoin(result.url, attr)
            if url is not None and url not in urls:
                urls.add(url)
                context.emit(rule='crawl', data={
                    'url': url
                })


@operation()
def parse(context, data):
    with context.http.rehash(data) as result:
        if result.html is not None:
            parse_html(context, data, result)

        rules = context.params.get('rules') or {'match_all': {}}
        if Rule.get_rule(rules).apply(result):
            context.emit(data=data)
