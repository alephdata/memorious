import logging
from six.moves.urllib.parse import urljoin
from banal import ensure_list
from urlnormalizer import normalize_url
from normality import collapse_spaces

from memorious.helpers.rule import Rule
from memorious.helpers.dates import iso_date
from memorious.util import make_key


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


def parse_for_metadata(context, data, result):
    meta = context.params.get('meta', {})
    date = context.params.get('meta_date', {})

    meta_paths = meta
    meta_paths.update(date)

    for key, xpaths in meta_paths.items():
        meta = parse_xpaths(result.html, key, date.keys(), xpaths)
        if meta is not None:
            context.log.info("Metadata extracted [%s]: %s" % (
                key, meta[key]))
            data.update(meta)

    return data


def parse_xpaths(html, key, dates, xpaths):
    data = {}
    for xpath in ensure_list(xpaths):
        if html.find(xpath) is not None:
            value = collapse_spaces(html.find(xpath).text_content())
            if key in dates:
                value = iso_date(value)
            data[key] = value
            # Takes the value from the first xpath in the list that is present.
            return data
    return None


def parse(context, data):
    with context.http.rehash(data) as result:
        if result.html is not None:
            parse_html(context, data, result)

            # Get extra metadata from the DOM
            if context.params.get('meta') is not None or context.params.get('meta_date') is not None:
                meta = parse_for_metadata(context, data, result)
                data.update(meta)

        rules = context.params.get('store') or {'match_all': {}}
        if Rule.get_rule(rules).apply(result):
            context.emit(rule='store', data=data)
