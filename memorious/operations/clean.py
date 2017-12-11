from normality import collapse_spaces
from banal import ensure_list
from lxml import html


def clean_html(context, data):
    """Clean an HTML DOM and store the changed version."""
    with context.http.rehash(data) as result:
        if not result.ok:
            context.emit(data=data)
            return
        doc = result.html

    if doc is None:
        context.emit(data=data)
        return

    remove_paths = context.params.get('remove_paths')
    for path in ensure_list(remove_paths):
        for el in doc.findall(path):
            el.drop_tree()

    html_text = html.tostring(doc, pretty_print=True)
    content_hash = context.store_data(html_text)
    data['content_hash'] = content_hash
    context.emit(data=data)
