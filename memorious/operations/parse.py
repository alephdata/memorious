import logging
from banal import ensure_list
from urllib.parse import urljoin
from normality import collapse_spaces
from servicelayer.cache import make_key

from memorious.helpers.rule import Rule
from memorious.helpers.dates import iso_date


log = logging.getLogger(__name__)
URL_TAGS = [('.//a', 'href'),
            ('.//img', 'src'),
            ('.//link', 'href'),
            ('.//iframe', 'src')]


def parse_html(context, data, result):
    context.log.info('Parse: %r', result.url)

    for title in result.html.xpath('.//title/text()'):
        if title is not None and 'title' not in data:
            data['title'] = title

    include = context.params.get('include_paths')
    if include is None:
        roots = [result.html]
    else:
        roots = []
        for path in include:
            roots = roots + result.html.xpath(path)

    seen = set()
    for root in roots:
        for tag_query, attr_name in URL_TAGS:
            for element in root.xpath(tag_query):
                attr = element.get(attr_name)
                if attr is None:
                    continue

                try:
                    url = urljoin(result.url, attr)
                    key = url
                except Exception:
                    log.warning('Invalid URL: %r', attr)
                    continue

                if url is None or key is None or key in seen:
                    continue
                seen.add(key)

                tag = make_key(context.run_id, key)
                if context.check_tag(tag):
                    continue
                context.set_tag(tag, None)
                data['url'] = url

                if data.get('title') is None:
                    # Option to set the document title from the link text.
                    if context.get('link_title', False):
                        data['title'] = collapse_spaces(element.text_content())
                    elif element.get('title'):
                        data['title'] = collapse_spaces(element.get('title'))

                context.http.session.headers['Referer'] = url
                context.emit(rule='fetch', data=data)


def parse_for_metadata(context, data, html):
    meta = context.params.get('meta', {})
    meta_date = context.params.get('meta_date', {})

    meta_paths = meta
    meta_paths.update(meta_date)

    for key, xpaths in meta_paths.items():
        for xpath in ensure_list(xpaths):
            for element in ensure_list(html.xpath(xpath)):
                try:
                    value = collapse_spaces(element.text_content())
                except AttributeError:
                    # useful when element is an attribute
                    value = collapse_spaces(str(element))
                if key in meta_date:
                    value = iso_date(value)
                if value is not None:
                    data[key] = value
                break
    return data


def parse(context, data):
    with context.http.rehash(data) as result:
        if result.html is not None:
            # Get extra metadata from the DOM
            parse_for_metadata(context, data, result.html)
            parse_html(context, data, result)

        rules = context.params.get('store') or {'match_all': {}}
        if Rule.get_rule(rules).apply(result):
            context.emit(rule='store', data=data)
