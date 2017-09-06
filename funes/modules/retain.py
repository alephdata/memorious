from lxml import html
from funes.operation import operation
from funes.model.result import HTTPResult


@operation()
def retain(context, data):
    res, doc = _drop_paths(context, data.get('res'))
    if res is None or doc is None:
        return
    meta = data.get('meta') or {}
    meta['crawler'] = context.crawler.name
    if 'html' in res.content_type:
        title = doc.findtext('.//title')
        if title is not None:
            meta['title'] = title
    meta['source_url'] = res.url
    meta['foreign_id'] = res.foreign_id
    if res.file_name and len(res.file_name.strip()) > 2:
        meta['file_name'] = '%s.html' % res.file_name
    meta['content_type'] = res.content_type
    meta['headers'] = res.headers
    data['meta'] = meta
    context.log.info("[Metadata created]: %s", res.url)
    context.emit(data=data)


def _drop_paths(context, res):
    with open(res.get(), 'r') as fh:
        doc = html.fromstring(fh.read())
    if res is not None and 'html' in res.content_type:
        check_path = context.params.get('check_path')
        if check_path is not None:
            if doc.find(check_path) is None:
                context.log.info("[Failed XML path check]: %r", res.url)
                return None

        for path in context.params.get('remove_paths', []):
            for el in doc.findall(path):
                el.drop_tree()
        foreign_id = res.foreign_id
        if foreign_id is None:
            foreign_id = res.url
        foreign_id = foreign_id + '-paths-removed'
        content = html.tostring(doc)
        res = HTTPResult.from_res(res, content=content, foreign_id=foreign_id)
    return res, doc
