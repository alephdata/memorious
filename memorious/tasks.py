from memorious.core import manager, celery as app
from memorious.core import init_memorious
from memorious.logic.context import handle  # noqa


init_memorious()


@app.task
def process_schedule():
    manager.run_scheduled()


@app.task
def run_cleanup():
    manager.run_cleanup()
