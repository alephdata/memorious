import logging
from banal import ensure_list
from urllib.parse import urljoin
from urlnormalizer import normalize_url
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

    title = result.html.findtext('.//title')
    if title is not None and 'title' not in data:
        data['title'] = title

    include = context.params.get('include_paths')
    if include is None:
        roots = [result.html]
    else:
        roots = []
        for path in include:
            roots = roots + result.html.findall(path)

    seen = set()
    for root in roots:
        for tag_query, attr_name in URL_TAGS:
            for element in root.findall(tag_query):
                attr = element.get(attr_name)
                if attr is None:
                    continue

                try:
                    url = normalize_url(urljoin(result.url, attr))
                except Exception:
                    log.warning('Invalid URL: %r', attr)
                    continue

                if url is None or url in seen:
                    continue
                seen.add(url)

                tag = make_key(context.run_id, url)
                if context.check_tag(tag):
                    continue
                context.set_tag(tag, None)
                data = {'url': url}
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
            element = html.find(xpath)
            if element is None:
                continue
            value = collapse_spaces(element.text_content())
            if key in meta_date:
                value = iso_date(value)
            if value is not None:
                data[key] = value
            break

    return data


def parse(context, data):
    with context.http.rehash(data) as result:
        if result.html is not None:
            parse_html(context, data, result)

            # Get extra metadata from the DOM
            parse_for_metadata(context, data, result.html)

        rules = context.params.get('store') or {'match_all': {}}
        if Rule.get_rule(rules).apply(result):
            context.emit(rule='store', data=data)
