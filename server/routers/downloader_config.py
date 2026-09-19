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

AUDIO_MIME_TYPES = ["audio/mpeg", "audio/wav", "audio/flac", "audio/aac", "audio/amr"]
VIDEO_MIME_TYPES = {
    # 常见网页和移动端视频
    "video/mp4",  # .mp4
    "video/webm",  # .webm
    "video/quicktime",  # .mov
    "video/x-m4v",  # .m4v

    # Matroska、AVI 和 Windows 视频
    "video/x-matroska",  # .mkv
    "video/mkv",  # 部分客户端会这样上报
    "video/x-msvideo",  # .avi
    "video/vnd.avi",  # AVI 的另一种 MIME 类型
    "video/avi",  # 部分客户端会这样上报
    "video/x-ms-wmv",  # .wmv
    "video/x-ms-asf",  # .asf

    # 常见传统视频格式
    "video/mpeg",  # .mpeg、.mpg
    "video/ogg",  # .ogv
    "video/x-flv",  # .flv
    "video/x-f4v",  # .f4v
    "video/x-dv",  # .dv

    # 手机、电视和传输流视频
    "video/3gpp",  # .3gp
    "video/3gpp2",  # .3g2
    "video/mp2t",  # .ts、.mts、.m2ts
    "video/x-ms-vob",  # .vob

    # 较少见的视频格式
    "video/vnd.rn-realvideo",  # .rv、.rmvb
    "video/h264",  # 裸 H.264 视频流
    "video/h265",  # 裸 H.265 / HEVC 视频流
}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB


@router.post("/upload_video")
async def upload_video(files: list[UploadFile] = File(...)):
    ret_list = []
    for file in files:
        if file.content_type not in VIDEO_MIME_TYPES:
            return result_failure(const.TASK_CONFIG_ERR_INVALID_FILE_FORMAT, "Uploaded file must be in video format")
        # Read content to check size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            return result_failure(const.TASK_CONFIG_ERR_FILE_SIZE_LIMIT_EXCEEDED,
                                  "Uploaded file size cannot exceed 500MB, filename: " + file.filename)
        suffix = Path(file.filename).suffix
        saved_name = f"{uuid.uuid4().hex}{suffix}"
        upload_path = await get_download_path()
        dest = Path(upload_path) / saved_name
        async with aiofiles.open(dest, "wb") as f:
            await f.write(content)
        abs_saved_name = os.path.join(_config.config['storage']['download'], saved_name)
        ret_dict = {
            "filename": file.filename,
            "saved_as": abs_saved_name,
            "size": len(content),
            "content_type": file.content_type,
        }
        ret_list.append(ret_dict)
    return result_succ(ret_list)
