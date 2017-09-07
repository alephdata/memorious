from lxml import html
from urlparse import urljoin
from funes.operation import operation
from funes.modules.extras.rule import Rule

URL_TAGS = [('a', 'href'),
            ('img', 'src'),
            ('link', 'href'),
            ('iframe', 'src')]


def parse_html(context, data, res):
    with res.load() as fh:
        doc = html.parse(fh)

    context.log.info('[Parsing]: %r', res.url)

    title = doc.findtext('.//title')
    if title is not None:
        data['title'] = title

    urls = set([])
    for tag_name, attr_name in URL_TAGS:
        for tag in doc.findall('.//%s' % tag_name):
            attr = tag.get(attr_name)
            if attr is None:
                continue
            url = urljoin(res.url, attr)
            if url is not None and url not in urls:
                urls.add(url)
                context.emit(rule='crawl', data={
                    'url': url,
                    'crawl_path': data.get('crawl_path', [])
                })

    return data


@operation()
def parse(context, data):
    res = data.get('res')
    if 'html' in res.content_type:
        data = parse_html(context, data, res)

    rules = context.params.get('rules', {'match_all': {}})
    if Rule.get_rule(rules).apply(res):
        context.emit(data=data)
