"""Task state management — supports in-memory and Redis backends."""

import ast
from abc import ABC, abstractmethod

from app.models import const


class BaseState(ABC):
    """Abstract state manager for task tracking."""

    @abstractmethod
    def update_task(self, task_id: str, state: int = const.TASK_STATE_PROCESSING, progress: int = 0, **kwargs):
        pass

    @abstractmethod
    def get_task(self, task_id: str):
        pass

    @abstractmethod
    def get_all_tasks(self, page: int, page_size: int):
        pass

    @abstractmethod
    def delete_task(self, task_id: str):
        pass


class MemoryState(BaseState):
    """In-memory state storage (default)."""

    def __init__(self):
        self._tasks = {}

    def get_all_tasks(self, page: int, page_size: int):
        start = (page - 1) * page_size
        end = start + page_size
        tasks = list(self._tasks.values())
        total = len(tasks)
        return tasks[start:end], total

    def update_task(self, task_id: str, state: int = const.TASK_STATE_PROCESSING,
                    progress: int = 0, **kwargs):
        progress = min(int(progress), 100)
        existing = self._tasks.get(task_id, {})
        # Append log entry if provided; preserve existing logs across updates
        logs = list(existing.get("logs", []))
        if "log" in kwargs:
            logs.append(kwargs.pop("log"))
        # Merge: preserve existing fields, overlay new kwargs, always set core fields last
        self._tasks[task_id] = {**existing, **kwargs,
                                "task_id": task_id, "state": state,
                                "progress": progress, "logs": logs}

    def get_task(self, task_id: str):
        return self._tasks.get(task_id, None)

    def delete_task(self, task_id: str):
        self._tasks.pop(task_id, None)


class RedisState(BaseState):
    """Redis-backed state storage for distributed deployments."""

    def __init__(self, host="localhost", port=6379, db=0, password=None):
        import redis as rd
        self._redis = rd.StrictRedis(host=host, port=port, db=db, password=password)

    def get_all_tasks(self, page: int, page_size: int):
        start = (page - 1) * page_size
        end = start + page_size
        tasks = []
        cursor = 0
        total = 0
        while True:
            cursor, keys = self._redis.scan(cursor, count=page_size)
            batch_start = total
            batch_size = len(keys)
            total += batch_size
            if batch_start < end and total > start:
                slice_start = max(0, start - batch_start)
                slice_end = min(batch_size, end - batch_start)
                for key in keys[slice_start:slice_end]:
                    task_data = self._redis.hgetall(key)
                    task = {k.decode("utf-8"): self._convert(v) for k, v in task_data.items()}
                    tasks.append(task)
            if cursor == 0:
                break
        return tasks, total

    def update_task(self, task_id: str, state: int = const.TASK_STATE_PROCESSING,
                    progress: int = 0, **kwargs):
        progress = min(int(progress), 100)
        if "log" in kwargs:
            log_entry = kwargs.pop("log")
            raw = self._redis.hget(task_id, "logs")
            try:
                logs = ast.literal_eval(raw.decode("utf-8")) if raw else []
                if not isinstance(logs, list):
                    logs = []
            except Exception:
                logs = []
            logs.append(log_entry)
            kwargs["logs"] = logs
        fields = {"task_id": task_id, "state": state, "progress": progress, **kwargs}
        for field, value in fields.items():
            self._redis.hset(task_id, field, str(value))

    def get_task(self, task_id: str):
        task_data = self._redis.hgetall(task_id)
        if not task_data:
            return None
        return {k.decode("utf-8"): self._convert(v) for k, v in task_data.items()}

    def delete_task(self, task_id: str):
        self._redis.delete(task_id)

    @staticmethod
    def _convert(value):
        value_str = value.decode("utf-8")
        try:
            return ast.literal_eval(value_str)
        except (ValueError, SyntaxError):
            pass
        if value_str.isdigit():
            return int(value_str)
        return value_str


# Global state instance
from app.config import config as app_config

_cfg = app_config
state: BaseState = (
    RedisState(
        host=_cfg.app.redis_host,
        port=_cfg.app.redis_port,
        db=_cfg.app.redis_db,
        password=_cfg.app.redis_password,
    )
    if _cfg.app.enable_redis
    else MemoryState()
)
