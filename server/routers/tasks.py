import logging

from fastapi import APIRouter, Query

from pipeline.pipeline import pipeline
from utils import const
from utils.result import result_succ, result_failure

router = APIRouter(
    prefix="/tasks",
    tags=["任务模块"]
)


@router.get("/")
def get_tasks():
    return result_succ()


@router.post("/add")
def add_tasks():
    return {"message": "任务添加成功"}


@router.get("/config")
def get_task_config():
    # 
    return result_succ()


@router.get("/check")
async def check_task_url(url: str = Query(default="", min_length=1, max_length=300)):
    logging.info(f"Checking task url: {url}")
    if not await pipeline.check(url):
        return result_failure(const.TASK_ERR_CHECK_URL, f"任务 url 检查失败，{url}")
    return result_succ()
