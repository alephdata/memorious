from banal import ensure_list
from lxml import html


def _get_html_document(context, data):
    with context.http.rehash(data) as result:
        if result.ok:
            return result.html


def clean_html(context, data):
    """Clean an HTML DOM and store the changed version."""
    doc = _get_html_document(context, data)
    if doc is None:
        context.emit(data=data)
        return

    remove_paths = context.params.get('remove_paths')
    for path in ensure_list(remove_paths):
        for el in doc.xpath(path):
            el.drop_tree()

    html_text = html.tostring(doc, pretty_print=True)
    content_hash = context.store_data(html_text)
    data['content_hash'] = content_hash
    context.emit(data=data)
