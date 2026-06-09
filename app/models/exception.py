"""Custom HTTP exception for structured error responses."""

from fastapi import HTTPException


class HttpException(HTTPException):
    def __init__(self, task_id: str = "", status_code: int = 400, message: str = "error", data=None):
        self.task_id = task_id
        self.data = data
        self.status_code = status_code
        self.message = message
        super().__init__(status_code=status_code, detail=message)
