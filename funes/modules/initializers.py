from banal import ensure_list

from funes.operation import operation


@operation()
def seed(context, data):
    for key in ('url', 'urls'):
        for url in ensure_list(context.params.get(key)):
            context.emit(data={'url': url})


@operation()
def sequence(context, data):
    start = context.params.get('start') or 1
    stop = context.params.get('stop')
    step = context.params.get('step') or 1
    for number in xrange(start, stop, step):
        context.emit(data={'number': number})
