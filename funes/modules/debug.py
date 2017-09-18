from pprint import pformat

from funes.operation import operation


@operation()
def output(context, data):
    context.log.info(pformat(data))
    context.emit(rule='pass', data=data)