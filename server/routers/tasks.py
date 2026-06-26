import json
import logging
import os.path
import aiofiles

from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from pipeline.pipeline import pipeline
from utils import const
from utils.database import database
from utils.exception import VPTException
from utils.gen_config import gen_config
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
async def get_task_config(db: AsyncSession = Depends(database.get_db)):
    if not os.path.exists("config.result"):
        await gen_config(db)
    try:
        async with aiofiles.open("config.result", mode="r", encoding="utf-8") as f:
            if not f:
                return result_failure(const.TASK_CONFIG_ERR_CONFIG_FILE, "任务配置文件未生成")
            ret_dict = json.loads(await f.read())
            return result_succ(ret_dict)
    except VPTException as e:
        return result_failure(const.TASK_CONFIG_ERR_CONFIG_FILE, f"任务配置文件未生成，{e}")


@router.get("/check")
async def check_task_url(url: str = Query(default="", min_length=1, max_length=300)):
    logging.info(f"Checking task url: {url}")
    if not await pipeline.check(url):
        return result_failure(const.TASK_ERR_CHECK_URL, f"任务 url 检查失败，{url}")
    return result_succ()
