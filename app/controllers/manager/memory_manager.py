"""InMemoryTaskManager — uses Python queue.Queue for task scheduling."""

from queue import Queue
from typing import Any

from app.controllers.manager.base_manager import TaskManager


class InMemoryTaskManager(TaskManager):
    def create_queue(self):
        return Queue(maxsize=self.max_queued_tasks)

    def enqueue(self, task: dict):
        self.queue.put(task)

    def dequeue(self) -> dict[str, Any] | None:
        return self.queue.get()

    def is_queue_empty(self) -> bool:
        return self.queue.empty()

    def queue_size(self) -> int:
        return self.queue.qsize()
