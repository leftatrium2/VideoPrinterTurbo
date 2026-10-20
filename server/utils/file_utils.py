import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

import anyio

import config.config as _config
from utils import const
from utils.exception import VPTException

logger = logging.getLogger(__name__)


def get_file_size(audio_path: str) -> int:
    """返回文件大小（字节）"""
    return os.path.getsize(audio_path)


def get_current_path() -> str:
    return _config.get_current_path()


def get_absolute_path(path: str) -> str:
    target = Path(path).expanduser()
    if not target.is_absolute():
        target = Path(get_current_path()) / target
    return str(target.resolve())


def get_relative_path(path: str) -> str:
    return Path(get_absolute_path(path)).relative_to(Path(get_current_path()).resolve()).as_posix()


async def get_storage_path() -> Optional[str]:
    path = _config.config['storage']['path']
    if not path:
        return None
    path = get_absolute_path(path)
    await anyio.to_thread.run_sync(lambda: Path(path).mkdir(parents=True, exist_ok=True))
    return path


async def get_model_path() -> Optional[str]:
    path = _config.config['storage']['models']
    if not path:
        return None
    path = get_absolute_path(path)
    await anyio.to_thread.run_sync(lambda: Path(path).mkdir(parents=True, exist_ok=True))
    return path


async def get_upload_path() -> Optional[str]:
    path = _config.config['storage']['upload']
    if not path:
        return None
    path = get_absolute_path(path)
    await anyio.to_thread.run_sync(lambda: Path(path).mkdir(parents=True, exist_ok=True))
    return path


async def get_download_path() -> Optional[str]:
    path = _config.config['storage']['download']
    if not path:
        return None
    path = get_absolute_path(path)
    await anyio.to_thread.run_sync(lambda: Path(path).mkdir(parents=True, exist_ok=True))
    return path


async def get_subtitle_path() -> Optional[str]:
    path = _config.config['storage']['subtitle']
    if not path:
        return None
    path = get_absolute_path(path)
    await anyio.to_thread.run_sync(lambda: Path(path).mkdir(parents=True, exist_ok=True))
    return path


async def get_video_to_text_path() -> Optional[str]:
    path = _config.config['storage']['video_to_text']
    if not path:
        return None
    path = get_absolute_path(path)
    await anyio.to_thread.run_sync(lambda: Path(path).mkdir(parents=True, exist_ok=True))
    return path


async def get_separate_vocals_path() -> Optional[str]:
    path = _config.config['storage']['audio_separator']
    if not path:
        return None
    path = get_absolute_path(path)
    await anyio.to_thread.run_sync(lambda: Path(path).mkdir(parents=True, exist_ok=True))
    return path


async def get_llm_rewrite_path() -> Optional[str]:
    path = _config.config['storage']['llm_rewrite']
    if not path:
        return None
    path = get_absolute_path(path)
    await anyio.to_thread.run_sync(lambda: Path(path).mkdir(parents=True, exist_ok=True))
    return path


async def get_tts_rewrite_path() -> Optional[str]:
    path = _config.config['storage']['tts_rewrite']
    if not path:
        return None
    path = get_absolute_path(path)
    await anyio.to_thread.run_sync(lambda: Path(path).mkdir(parents=True, exist_ok=True))
    return path


async def get_material_path() -> Optional[str]:
    path = _config.config['storage']['material']
    if not path:
        return None
    path = get_absolute_path(path)
    await anyio.to_thread.run_sync(lambda: Path(path).mkdir(parents=True, exist_ok=True))
    return path


async def get_output_path() -> Optional[str]:
    path = _config.config['storage']['output']
    if not path:
        return None
    path = get_absolute_path(path)
    await anyio.to_thread.run_sync(lambda: Path(path).mkdir(parents=True, exist_ok=True))
    return path


def get_resource_font_path() -> str:
    fonts_path = Path(
        os.environ.get("VPT_RESOURCE_DIR", get_current_path())).resolve() / "server" / "resources" / "fonts"
    return str(fonts_path)


def get_resource_bgm_path() -> str:
    fonts_path = Path(
        os.environ.get("VPT_RESOURCE_DIR", get_current_path())).resolve() / "server" / "resources" / "songs"
    return str(fonts_path)


async def remove_download_video(task_id: str):
    download_path = await get_download_path()
    if not download_path:
        return

    download_mp4_file = Path(download_path, f"{task_id}.mp4")
    download_mp3_file = Path(download_path, f"{task_id}.mp3")



    try:
        await anyio.to_thread.run_sync(lambda: download_mp4_file.unlink(missing_ok=True))
        await anyio.to_thread.run_sync(lambda: download_mp3_file.unlink(missing_ok=True))
    except Exception as ex:
        logger.error(f"Failed to remove download files for task {task_id}: {ex}")
        raise VPTException(
            code=const.GLOBAL_ERR_PATH_NOT_FOUND,
            message=f"Failed to remove download files: {ex}"
        ) from ex


if __name__ == "__main__":
    absolute_path = "/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/downloads/20260913190132110313.mp4"
    ret_relative_path = get_relative_path(absolute_path)
    logger.info(f"relative path: {ret_relative_path}")

    relative_path = "storage/downloads/20260913190132110313.mp4"
    ret_absolute_path = get_absolute_path(relative_path)
    logger.info(f"absolute path: {ret_absolute_path}")
