from lxml import html
from urlparse import urljoin
from funes.operation import operation
from funes.modules.extras.util import next_path


@operation()
def parse(context, data):
    tags = [('a', 'href'),
            ('img', 'src'),
            ('link', 'href'),
            ('iframe', 'src')]
    res = data.get('res')
    with open(res.get(), 'r') as fh:
        doc = html.fromstring(fh.read())
    context.log.info('[Parsing]: %r', res.url)

    urls = set([])
    for tag_name, attr_name in tags:
        for tag in doc.findall('.//%s' % tag_name):
            attr = tag.get(attr_name)
            if attr is None:
                continue
            url = urljoin(res.url, attr)
            if url is not None:
                urls.add(url)

    for url in urls:
        url_data = {}
        url_data['url'] = url
        url_data['path'] = next_path(data)
        url_data['crawl_rules'] = data.get('crawl_rules')
        url_data['retain_rules'] = data.get('retain_rules')
        context.emit(rule='retain', data=url_data)
