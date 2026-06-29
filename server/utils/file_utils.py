import asyncio
import os
from pathlib import Path

import anyio

import config.config as _config


def get_current_path():
    return f"{Path.cwd().parent}"


async def get_storage_path() -> str or None:
    path = _config.config['storage']['path']
    if not path:
        return None
    path = os.path.join(get_current_path(), path)
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


async def get_upload_path() -> str or None:
    path = _config.config['storage']['upload']
    if not path:
        return None
    path = os.path.join(get_current_path(), path)
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


async def get_download_path() -> str or None:
    path = _config.config['storage']['download']
    if not path:
        return None
    path = os.path.join(get_current_path(), path)
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


async def get_video_to_text_path() -> str or None:
    path = _config.config['storage']['video_to_text']
    if not path:
        return None
    path = os.path.join(get_current_path(), path)
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


async def get_llm_rewrite_path() -> str or None:
    path = _config.config['storage']['llm_rewrite']
    if not path:
        return None
    path = os.path.join(get_current_path(), path)
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


async def get_material_path() -> str or None:
    path = _config.config['storage']['material']
    if not path:
        return None
    path = os.path.join(get_current_path(), path)
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


async def get_output_path() -> str or None:
    path = _config.config['storage']['output']
    if not path:
        return None
    path = os.path.join(get_current_path(), path)
    await anyio.to_thread.run_sync(lambda: os.makedirs(path, exist_ok=True))
    return path


async def main():
    _config.init_config()
    await get_output_path()


if __name__ == "__main__":
    result = asyncio.run(main())
    print(result)
