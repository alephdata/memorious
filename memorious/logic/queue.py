import logging
from threading import Thread
from six.moves.queue import Queue


log = logging.getLogger(__name__)


class CrawlerExecutionQueue(object):
    """Queue and execute operations in a separate thread when celery is
    running in eager mode.
    """
    def __init__(self):
        self.queue = Queue()

    def queue_operation(self, context, data):
        if not hasattr(self, 'worker'):
            self.worker = Thread(target=self.execute_crawler)
            self.worker.setDaemon(True)
            self.worker.start()
        self.queue.put((context, data))

    def execute_crawler(self):
        while True:
            context, data = self.queue.get()
            context.execute(data)
            self.queue.task_done()

    @property
    def is_empty(self):
        return not self.queue.unfinished_tasks
