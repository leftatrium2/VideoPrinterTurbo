from pydantic import BaseModel


class Task(BaseModel):
    task_url: str = ""
    is_deleted: int = 0
    status: int = 0
    task_id: int = 0

