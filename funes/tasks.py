from funes.core import manager, celery as app
from funes.context import handle  # noqa


@app.task
def process_schedule():
    manager.run_scheduled()
