from urlparse import urljoin, urlparse
from memorious.helpers.rule import Rule
from memorious.util import normalize_url, make_key


URL_TAGS = [('.//a', 'href'),
            ('.//img', 'src'),
            ('.//link', 'href'),
            ('.//iframe', 'src')]


def parse_html(context, data, result):
    context.log.info('Parse: %r', result.url)

    title = result.html.findtext('.//title')
    if title is not None and 'title' not in data:
        data['title'] = title

    seen = set()
    for tag_query, attr_name in URL_TAGS:
        for element in result.html.findall(tag_query):
            attr = element.get(attr_name)
            if attr is None:
                continue

            url = normalize_url(urljoin(result.url, attr))
            if url in seen:
                continue
            seen.add(url)
            parsed = urlparse(url)
            if parsed.scheme.lower() not in ['http', 'https']:
                continue

            tag = make_key((context.run_id, url))
            if context.check_tag(tag):
                continue
            context.set_tag(tag, None)

            data = {'url': url}
            if element.get('title'):
                data['title'] = element.get('title')
            context.emit(rule='fetch', data=data)


def parse(context, data):
    with context.http.rehash(data) as result:
        if result.html is not None:
            parse_html(context, data, result)

        rules = context.params.get('store') or {'match_all': {}}
        if Rule.get_rule(rules).apply(result):
            context.emit(rule='store', data=data)
