from funes.operation import operation


@operation()
def webcrawler(context, data):
    context.emit(data={
        'url': context.params.get('seed_url')
    })
