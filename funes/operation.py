from datetime import datetime
from functools import wraps

from funes.core import session
from funes.model.event import Event
from funes.model.op import Operation


def operation(name=None, isolate=True):
    """Wrap a method on a crawler to track the outcome of its execution."""
    def op_decorator(func):
        @wraps(func)
        def func_wrapper(context, data, *a, **kw):
            started_at = datetime.utcnow()
            status = Operation.STATUS_SUCCESS
            run_id = context.run_id
            ended_at = None
            operation_id = Operation.id
            context.operation_id = operation_id
            try:
                if context.sender is None:
                    context.sender = func.__name__
                return func(context, data, *a, **kw)
            except Exception as exc:
                status = Operation.STATUS_FAILED
                if not isolate:
                    raise
                context.log.exception(exc)
                ended_at = datetime.utcnow()
                Event.emit(context.name, run_id=run_id, operation_id=operation_id, # noqa
                           operation=func.__name__, exc=exc, timestamp=ended_at) # noqa
            finally:
                context.log.info('[Running]: %s', func.__name__)
                if ended_at is None:
                    ended_at = datetime.utcnow()
                op = Operation()
                op.crawler = context.name
                op.run_id = run_id
                op.operation = func.__name__
                op.scope = Operation.SCOPE_METHOD
                op.status = status
                op.started_at = started_at
                op.ended_at = ended_at
                session.add(op)
                session.commit()
        return func_wrapper
    return op_decorator
