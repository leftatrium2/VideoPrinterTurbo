import asyncio
import os

import anyio

from config.config import config


async def get_storage_path() -> str or None:
    path = config['storage']['path']
    if not path:
        return None
    path = os.getcwd() + os.sep + path
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


async def get_download_path() -> str or None:
    path = config['storage']['download']
    if not path:
        return None
    path = os.getcwd() + os.sep + path
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


async def get_video_to_text_path() -> str or None:
    path = config['storage']['video_to_text']
    if not path:
        return None
    path = os.getcwd() + os.sep + path
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


async def get_llm_rewrite_path() -> str or None:
    path = config['storage']['llm_rewrite']
    if not path:
        return None
    path = os.getcwd() + os.sep + path
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


async def get_material_path() -> str or None:
    path = config['storage']['material']
    if not path:
        return None
    path = os.getcwd() + os.sep + path
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


async def get_output_path() -> str or None:
    path = config['storage']['output']
    if not path:
        return None
    path = os.getcwd() + os.sep + path
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


if __name__ == "__main__":
    result = asyncio.run(get_output_path())
    print(result)
