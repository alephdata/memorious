from funes.operation import operation


@operation()
def seed(context, data):
    context.emit(data={
        'url': context.params.get('url')
    })
