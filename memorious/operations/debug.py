from pprint import pformat


def inspect(context, data):
    context.log.info(pformat(data))
    context.emit(data=data, optional=True)
