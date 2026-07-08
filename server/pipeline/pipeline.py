import asyncio
import importlib
import logging

from sqlalchemy import select

import config.config as _config
from models.model import VptTask
from pipeline.downloader.base import DownloaderContext, BaseDownloader
from pipeline.downloader.yt_dlp.yt_dlp_downloader import YtDlpDownloader
from utils.database import database

downloaders = {}


def init_downloader():
    global downloaders
    for k, v in _config.downloader_config.items():
        v = v.strip()
        module_path, class_name = v.rsplit(".", 1)
        cls = getattr(importlib.import_module(module_path), class_name)
        downloaders[k] = cls()
    downloaders['others'] = YtDlpDownloader()
    print(downloaders)


async def get_downloader(url: str) -> BaseDownloader or None:
    if not url:
        return None
    for k, v in _config.downloader_config.items():
        keyword = k.lower().strip()
        if keyword in url:
            if k not in downloaders:
                logging.error("cant find the downloader, maybe it not init, keyword: ", k)
                return None
            return downloaders[k]

    return downloaders['others']


class Pipeline:
    def __init__(self):
        pass

    # 检查 视频url 是否可下载
    async def check(self, url: str) -> bool:
        if not url.strip():
            logging.error("Url is empty")
            return False
        downloader = await get_downloader(url)
        if not downloader:
            logging.error("Downloader is None")
            return False
        return await downloader.check(url)

    # 下载视频
    async def download(self, url: str, output_dir: str, ctx: DownloaderContext) -> str or None:
        if not url.strip():
            logging.error("Url is empty")
            return None
        downloader = await get_downloader(url)
        if not downloader:
            logging.error("Downloader is None")
            return None
        return await downloader.download(url, output_dir, ctx)


pipeline = Pipeline()


async def main():
    task_id = "20260701212108501553"
    database.start()
    db = database.get_db()
    result = await db.execute(select(VptTask).where(
        VptTask.task_id == task_id,
        VptTask.is_deleted == 0
    ).order_by(VptTask.create_time.asc()).limit(1))
    item = result.scalar_one_or_none()
    print(item)


if __name__ == "__main__":
    asyncio.run(main())
