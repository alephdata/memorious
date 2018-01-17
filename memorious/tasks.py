from memorious.core import manager, celery as app, session
from memorious.logic.context import handle  # noqa
from memorious.model import Operation, CrawlerReport


@app.task
def process_schedule():
    manager.run_scheduled()


@app.task
def sync_crawler_stat():
    """Update the crawler_report table based on current operation table data"""
    CrawlerReport.sync_crawler_stat()
