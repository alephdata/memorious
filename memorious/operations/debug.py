from pprint import pformat

from memorious.operation import operation


@operation()
def inspect(context, data):
    context.log.info(pformat(data))
    context.emit(rule='pass', data=data)