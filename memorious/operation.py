from datetime import datetime
from functools import wraps

from memorious.core import session
from memorious.model.event import Event
from memorious.model.operation import Operation


def operation():
    """Wrap a method on a crawler to track the outcome of its execution."""
    def op_decorator(func):

        @wraps(func)
        def func_wrapper(context, data, *a, **kw):
            op = Operation()
            op.crawler = context.crawler.name
            op.name = context.stage.name
            op.run_id = context.run_id
            op.status = Operation.STATUS_PENDING
            session.add(op)
            session.commit()

            context.operation_id = op.id

            try:
                context.log.info('Running: %s', op.name)
                res = func(context, data, *a, **kw)
                op.status = Operation.STATUS_SUCCESS
                return res
            except Exception as exc:
                # this should clear results and tags created by this op
                session.rollback()
                Event.save(op.id, Event.LEVEL_ERROR, exc=exc)
                context.log.exception(exc)
            finally:
                if op.status == Operation.STATUS_PENDING:
                    op.status = Operation.STATUS_FAILED
                op.ended_at = datetime.utcnow()
                session.add(op)
                session.commit()

        return func_wrapper
    return op_decorator
