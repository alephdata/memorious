from banal import ensure_list

from funes.operation import operation


@operation()
def seed(context, data):
    for key in ('url', 'urls'):
        for url in ensure_list(context.params.get(key)):
            context.emit(data={'url': url})
