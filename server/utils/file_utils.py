import asyncio
import os
from typing import Optional

import anyio

import config.config as _config


def get_file_size(audio_path: str) -> int:
    """返回文件大小（字节）"""
    return os.path.getsize(audio_path)


def get_current_path() -> str:
    return _config.get_current_path()


def get_absolute_path(path: str) -> str:
    return os.path.join(get_current_path(), path)


def get_relative_path(path: str) -> str:
    return path.replace(get_current_path(), "").strip("/")


async def get_storage_path() -> Optional[str]:
    path = _config.config['storage']['path']
    if not path:
        return None
    path = os.path.join(get_current_path(), path)
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


async def get_upload_path() -> Optional[str]:
    path = _config.config['storage']['upload']
    if not path:
        return None
    path = os.path.join(get_current_path(), path)
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


async def get_download_path() -> Optional[str]:
    path = _config.config['storage']['download']
    if not path:
        return None
    path = os.path.join(get_current_path(), path)
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


async def get_subtitle_path() -> Optional[str]:
    path = _config.config['storage']['subtitle']
    if not path:
        return None
    path = os.path.join(get_current_path(), path)
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


async def get_video_to_text_path() -> Optional[str]:
    path = _config.config['storage']['video_to_text']
    if not path:
        return None
    path = os.path.join(get_current_path(), path)
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


async def get_llm_rewrite_path() -> Optional[str]:
    path = _config.config['storage']['llm_rewrite']
    if not path:
        return None
    path = os.path.join(get_current_path(), path)
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


async def get_tts_rewrite_path() -> Optional[str]:
    path = _config.config['storage']['tts_rewrite']
    if not path:
        return None
    path = os.path.join(get_current_path(), path)
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


async def get_material_path() -> Optional[str]:
    path = _config.config['storage']['material']
    if not path:
        return None
    path = os.path.join(get_current_path(), path)
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


async def get_output_path() -> Optional[str]:
    path = _config.config['storage']['output']
    if not path:
        return None
    path = os.path.join(get_current_path(), path)
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


if __name__ == "__main__":
    absolute_path = "/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/downloads/20260913190132110313.mp4"
    ret_relative_path = get_relative_path(absolute_path)
    print(f"relative path: {ret_relative_path}")

    relative_path = "storage/downloads/20260913190132110313.mp4"
    ret_absolute_path = get_absolute_path(relative_path)
    print(f"absolute path: {ret_absolute_path}")
