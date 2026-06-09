"""RedisTaskManager — uses Redis List for distributed task scheduling."""

import json
from typing import Any

from app.controllers.manager.base_manager import TaskManager
from app.models.schema import VideoRewriteParams
from app.services import task as tm


FUNC_MAP = {
    "start": tm.start,
}


class RedisTaskManager(TaskManager):
    def __init__(self, max_concurrent_tasks: int, redis_url: str, max_queued_tasks: int = 100):
        import redis as rd
        self.redis_client = rd.Redis.from_url(redis_url)
        super().__init__(max_concurrent_tasks, max_queued_tasks=max_queued_tasks)

    def create_queue(self):
        return "task_queue"

    def enqueue(self, task: dict):
        task_copy = task.copy()
        if "params" in task["kwargs"] and isinstance(task["kwargs"]["params"], VideoRewriteParams):
            task_copy["kwargs"]["params"] = task["kwargs"]["params"].dict()
        task_copy["func"] = task["func"].__name__
        self.redis_client.rpush(self.queue, json.dumps(task_copy))

    def dequeue(self) -> dict[str, Any] | None:
        task_json = self.redis_client.lpop(self.queue)
        if task_json:
            task_info = json.loads(task_json)
            task_info["func"] = FUNC_MAP.get(task_info["func"])
            if "params" in task_info.get("kwargs", {}) and isinstance(task_info["kwargs"]["params"], dict):
                task_info["kwargs"]["params"] = VideoRewriteParams(**task_info["kwargs"]["params"])
            return task_info
        return None

    def is_queue_empty(self) -> bool:
        return self.redis_client.llen(self.queue) == 0

    def queue_size(self) -> int:
        return self.redis_client.llen(self.queue)
