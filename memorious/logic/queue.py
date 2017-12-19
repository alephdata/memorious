import logging
from threading import Thread
from Queue import Queue


log = logging.getLogger(__name__)


class CrawlerExecutionQueue(object):
    def __init__(self):
        self.queue = Queue()
        worker = Thread(target=self.execute_crawler)
        worker.setDaemon(True)
        worker.start()

    def queue_crawler(self, context, data):
        self.queue.put((context, data))

    def execute_crawler(self):
        while True:
            context, data = self.queue.get()
            context.execute(data)
            self.queue.task_done()

    @property
    def is_empty(self):
        return not self.queue.unfinished_tasks
