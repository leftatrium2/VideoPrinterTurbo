"""Video rewrite controller — API endpoints for rewrite tasks."""

import glob
import os
import pathlib
import shutil
from typing import Union

from fastapi import BackgroundTasks, Path, Query, Request, UploadFile
from fastapi.params import File
from fastapi.responses import FileResponse, StreamingResponse
from loguru import logger

from app.config import config
from app.controllers import base
from app.controllers.manager.base_manager import TaskQueueFullError
from app.controllers.manager.memory_manager import InMemoryTaskManager
from app.controllers.manager.redis_manager import RedisTaskManager
from app.controllers.v1.base import new_router
from app.models.exception import HttpException
from app.models.schema import (
    BaseResponse,
    TaskDeletionResponse,
    TaskQueryRequest,
    TaskQueryResponse,
    TaskResponse,
    VideoRewriteParams,
)
from app.services import state as sm
from app.services import task as tm
from app.utils import file_security, utils

router = new_router()

# Task manager setup
_enable_redis = config.app.enable_redis
_max_concurrent = config.app.max_concurrent_tasks
_max_queued = config.app.max_queued_tasks

if _enable_redis:
    task_manager = RedisTaskManager(
        max_concurrent_tasks=_max_concurrent,
        redis_url=f"redis://:{config.app.redis_password}@{config.app.redis_host}:{config.app.redis_port}/{config.app.redis_db}",
        max_queued_tasks=_max_queued,
    )
else:
    task_manager = InMemoryTaskManager(
        max_concurrent_tasks=_max_concurrent,
        max_queued_tasks=_max_queued,
    )


def _sanitize_upload_filename(filename: str, request_id: str) -> str:
    normalized = (filename or "").replace("\\", "/").split("/")[-1].strip()
    if not normalized or normalized in {".", ".."}:
        raise HttpException(task_id=request_id, status_code=400, message=f"{request_id}: invalid filename")
    return normalized


def _resolve_path_within_directory(base_dir: str, unsafe_path: str, request_id: str) -> str:
    try:
        return file_security.resolve_path_within_directory(base_dir, unsafe_path)
    except ValueError as exc:
        logger.warning(f"reject unsafe path, request_id: {request_id}, path: {unsafe_path}, error: {exc}")
        raise HttpException(
            task_id=request_id,
            status_code=404 if str(exc).startswith("file does not exist") else 403,
            message=f"{request_id}: invalid file path",
        )


@router.post("/rewrite", response_model=TaskResponse, summary="Submit a video rewrite task")
def create_rewrite_task(request: Request, body: VideoRewriteParams):
    """Submit a new video rewriting task."""
    task_id = utils.get_uuid()
    request_id = base.get_task_id(request)
    try:
        task = {"task_id": task_id, "request_id": request_id, "params": body.model_dump()}
        sm.state.update_task(task_id)
        task_manager.add_task(tm.start, task_id=task_id, params=body)
        logger.success(f"Task created: {utils.to_json(task)}")
        return utils.get_response(200, task)
    except TaskQueueFullError as e:
        sm.state.delete_task(task_id)
        logger.warning(f"reject task, queue full, request_id: {request_id}, task_id: {task_id}")
        raise HttpException(task_id=task_id, status_code=429, message=f"{request_id}: {str(e)}")
    except ValueError as e:
        raise HttpException(task_id=task_id, status_code=400, message=f"{request_id}: {str(e)}")


@router.get("/tasks", response_model=TaskQueryResponse, summary="Get all tasks")
def get_all_tasks(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
):
    request_id = base.get_task_id(request)
    tasks, total = sm.state.get_all_tasks(page, page_size)
    response = {"tasks": tasks, "total": total, "page": page, "page_size": page_size}
    return utils.get_response(200, response)


@router.get("/tasks/{task_id}", response_model=TaskQueryResponse, summary="Query task status")
def get_task(
    request: Request,
    task_id: str = Path(..., description="Task ID"),
    query: TaskQueryRequest = None,
):
    request_id = base.get_task_id(request)
    endpoint = config.app.endpoint
    task = sm.state.get_task(task_id)
    if task:
        tasks_dir = utils.task_dir()
        response_task = dict(task)

        # Convert file paths to URIs
        for key in ("videos", "combined_videos", "output_video"):
            if key in task:
                file_list = task[key] if isinstance(task[key], list) else [task[key]]
                response_task[key] = [
                    _task_file_to_uri(v, endpoint, tasks_dir, request_id) for v in file_list
                ]
        return utils.get_response(200, response_task)

    raise HttpException(task_id=task_id, status_code=404, message=f"{request_id}: task not found")


def _task_file_to_uri(file: str, endpoint: str, task_dir: str, request_id: str) -> str:
    if not isinstance(file, str):
        return file
    if file.startswith(("http://", "https://")):
        return file
    try:
        resolved = file_security.resolve_path_within_directory(task_dir, file)
    except ValueError as exc:
        logger.warning(f"skip unsafe task output path, request_id: {request_id}, path: {file}, error: {exc}")
        return file

    relative = os.path.relpath(resolved, task_dir).replace("\\", "/")
    uri_path = f"tasks/{relative}"
    if endpoint:
        return f"{endpoint.rstrip('/')}/{uri_path}"
    return f"/{uri_path}"


@router.delete("/tasks/{task_id}", response_model=TaskDeletionResponse, summary="Delete a task")
def delete_task(request: Request, task_id: str = Path(..., description="Task ID")):
    request_id = base.get_task_id(request)
    task = sm.state.get_task(task_id)
    if task:
        tasks_dir = utils.task_dir()
        current_task_dir = os.path.join(tasks_dir, task_id)
        if os.path.exists(current_task_dir):
            shutil.rmtree(current_task_dir)
        sm.state.delete_task(task_id)
        logger.success(f"task deleted: {task_id}")
        return utils.get_response(200)

    raise HttpException(task_id=task_id, status_code=404, message=f"{request_id}: task not found")


@router.get("/musics", summary="List background music files")
def get_bgm_list(request: Request):
    suffix = "*.mp3"
    song_dir = utils.song_dir()
    files = glob.glob(os.path.join(song_dir, suffix))
    bgm_list = []
    for file in files:
        filename = os.path.basename(file)
        bgm_list.append({"name": filename, "size": os.path.getsize(file), "file": filename})
    return utils.get_response(200, {"files": bgm_list})


@router.get("/stream/{file_path:path}", summary="Stream a video file")
async def stream_video(request: Request, file_path: str):
    request_id = base.get_task_id(request)
    tasks_dir = utils.task_dir()
    video_path = _resolve_path_within_directory(tasks_dir, file_path, request_id)
    range_header = request.headers.get("Range")
    video_size = os.path.getsize(video_path)
    start, end = 0, video_size - 1

    if range_header:
        range_ = range_header.split("bytes=")[1]
        parts = range_.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if parts[1] else video_size - 1
        if start > end:
            start, end = 0, video_size - 1

    length = end - start + 1

    def file_iterator(file_path, offset, bytes_to_read):
        with open(file_path, "rb") as f:
            f.seek(offset)
            remaining = bytes_to_read
            while remaining > 0:
                chunk = min(4096, remaining)
                data = f.read(chunk)
                if not data:
                    break
                remaining -= len(data)
                yield data

    response = StreamingResponse(
        file_iterator(video_path, start, length), media_type="video/mp4"
    )
    response.headers["Content-Range"] = f"bytes {start}-{end}/{video_size}"
    response.headers["Accept-Ranges"] = "bytes"
    response.headers["Content-Length"] = str(length)
    response.status_code = 206
    return response


@router.get("/download/{file_path:path}", summary="Download a video file")
async def download_video(request: Request, file_path: str):
    request_id = base.get_task_id(request)
    tasks_dir = utils.task_dir()
    video_path = _resolve_path_within_directory(tasks_dir, file_path, request_id)
    p = pathlib.Path(video_path)
    filename = p.stem
    extension = p.suffix
    headers = {"Content-Disposition": f"attachment; filename={filename}{extension}"}
    return FileResponse(
        path=video_path,
        headers=headers,
        filename=f"{filename}{extension}",
        media_type=f"video/{extension[1:]}",
    )
