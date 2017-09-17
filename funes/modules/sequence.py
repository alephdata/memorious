from funes.operation import operation


@operation()
def sequence(context, data):
    start = context.params.get('start') or 1
    stop = context.params.get('stop')
    step = context.params.get('step') or 1
    for number in xrange(start, stop, step):
        context.emit(data={'number': number})
