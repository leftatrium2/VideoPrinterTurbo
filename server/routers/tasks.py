from fastapi import APIRouter

from utils.result import result_succ

router = APIRouter(
    prefix="/tasks",
    tags=["任务模块"]
)


@router.get("/")
def get_tasks():
    return result_succ([])


@router.post("/add")
def add_tasks():
    return {"message": "任务添加成功"}


@router.get("/config")
def get_task_config():
    return result_succ({})
