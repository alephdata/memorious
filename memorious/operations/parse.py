import random
from urlparse import urljoin, urlparse
from memorious.helpers.rule import Rule
from memorious.util import normalize_url


URL_TAGS = [('.//a', 'href'),
            ('.//img', 'src'),
            ('.//link', 'href'),
            ('.//iframe', 'src')]


def parse_html(context, data, result):
    context.log.info('Parse: %r', result.url)

    title = result.html.findtext('.//title')
    if title is not None and 'title' not in data:
        data['title'] = title

    urls = []
    for tag_query, attr_name in URL_TAGS:
        for tag in result.html.findall(tag_query):
            attr = tag.get(attr_name)
            if attr is None:
                continue
            url = normalize_url(urljoin(result.url, attr))
            parsed = urlparse(url)
            if parsed.scheme.lower() not in ['http', 'https']:
                continue
            if url not in urls:
                urls.append(url)

    random.shuffle(urls)
    for url in urls:
        if context.check_run_tag(url):
            continue
        context.set_run_tag(url, None)
        context.emit(rule='fetch', data={
            'url': url
        })


def parse(context, data):
    with context.http.rehash(data) as result:
        if result.html is not None:
            parse_html(context, data, result)

        rules = context.params.get('store') or {'match_all': {}}
        if Rule.get_rule(rules).apply(result):
            context.emit(rule='store', data=data)
