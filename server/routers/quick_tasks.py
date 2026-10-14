import logging

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from models.model import VptTasks
from models.schemas import QuickDownloadTaskItem
from utils import const
from utils.database import database
from utils.result import result_failure, result_succ
from utils.task_utils import gen_task_id

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/quick_tasks",
    tags=["Task Module"]
)

TEXT_MIME_TYPE = ["text/plain", "text/csv"]
MAX_FILE_SIZE = 100 * 1024  # 100KB


async def __add_single_task(item: QuickDownloadTaskItem, db: AsyncSession = Depends(database.get_db)):
    task = VptTasks(
        task_id=gen_task_id(),
        task_url=item.task_url,
        is_use_proxy=item.is_use_proxy
    )
    db.add(task)
    await db.commit()


@router.post("/multi_download")
async def add_multi_download_task(items: list[QuickDownloadTaskItem], db: AsyncSession = Depends(database.get_db)):
    if len(items) == 0:
        return result_failure(const.TASK_MULTI_DOWNLOAD_EMPTY, "Task items empty")
    if len(items) > 100:
        return result_failure(const.TASK_MULTI_DOWNLOAD_MAX_URL_NUM, "Task items size cannot exceed 100")
    for item in items:
        await __add_single_task(item, db=db)
    return result_succ()


@router.post("/multi_download_upload")
async def add_multi_download_upload_task(file: UploadFile = File(...), is_use_proxy: bool = Form(False),
                                         db: AsyncSession = Depends(database.get_db)):
    if file.content_type not in TEXT_MIME_TYPE:
        return result_failure(const.TASK_CONFIG_ERR_INVALID_FILE_FORMAT, "Uploaded file must be in text format")
    # Read content to check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        return result_failure(const.TASK_CONFIG_ERR_FILE_SIZE_LIMIT_EXCEEDED, "Uploaded file size cannot exceed 100MB")
    text = content.decode("utf-8")
    url_list = [line.strip() for line in text.splitlines() if line.strip()]
    for url in url_list:
        item = QuickDownloadTaskItem(task_url=url, is_use_proxy=is_use_proxy)
        await __add_single_task(item, db=db)
    return result_succ()
