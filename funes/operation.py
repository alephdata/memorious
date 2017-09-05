from datetime import datetime
from functools import wraps

from funes.core import session
from funes.model.event import Event
from funes.model.operation import Operation


def operation(name=None):
    """Wrap a method on a crawler to track the outcome of its execution."""
    def op_decorator(func):

        @wraps(func)
        def func_wrapper(context, data, *a, **kw):
            op = Operation()
            op.crawler = context.name
            op.name = name or func.__name__
            op.run_id = context.run_id
            op.status = Operation.STATUS_PENDING
            session.add(op)
            session.commit()

            context.operation_id = op.id
            context.sender = context.sender or op.name

            try:
                context.log.info('Running: %s', op.name)
                res = func(context, data, *a, **kw)
                op.status = Operation.STATUS_SUCCESS
                return res
            except Exception as exc:
                op.status = Operation.STATUS_FAILED
                Event.emit(op.id, Event.LEVEL_ERROR, exc=exc)
                context.log.exception(exc)
            finally:
                op.ended_at = datetime.utcnow()
                session.commit()
        return func_wrapper
    return op_decorator
