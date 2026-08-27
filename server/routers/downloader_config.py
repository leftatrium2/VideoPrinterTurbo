import os
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, UploadFile, File

from utils import const
from utils.file_utils import get_download_path
from utils.result import result_succ, result_failure
import config.config as _config

router = APIRouter(
    prefix="/downloader",
    tags=["Downloader Config Module"]
)

AUDIO_MIME_TYPE = ["audio/mpeg", "audio/wav", "audio/flac", "audio/aac", "audio/amr"]
VIDEO_MIME_TYPE = ["video/mp4", "video/mkv", "video/avi", "video/wmv", "video/flv"]
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB


@router.post("/upload_video")
async def upload_video(files: list[UploadFile] = File(...)):
    ret_list = []
    for file in files:
        if file.content_type not in VIDEO_MIME_TYPE:
            return result_failure(const.TASK_CONFIG_ERR_INVALID_FILE_FORMAT, "Uploaded file must be in video format")
        # Read content to check size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            return result_failure(const.TASK_CONFIG_ERR_FILE_SIZE_LIMIT_EXCEEDED,
                                  "Uploaded file size cannot exceed 500MB, filename: " + file.filename)
        content = await file.read()
        suffix = Path(file.filename).suffix
        saved_name = f"{uuid.uuid4().hex}{suffix}"
        upload_path = await get_download_path()
        dest = Path(upload_path) / saved_name
        async with aiofiles.open(dest, "wb") as f:
            await f.write(content)
        abs_saved_name = os.path.join(_config.config['storage']['upload'], saved_name)
        ret_dict = {
            "filename": file.filename,
            "saved_as": abs_saved_name,
            "size": len(content),
            "content_type": file.content_type,
        }
        ret_list.append(ret_dict)
    return result_succ(ret_list)
