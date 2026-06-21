import asyncio
import importlib
import logging

import config.config as _config
from pipeline.downloader.base import DownloaderContext, BaseDownloader
from pipeline.downloader.bilibili.bilibili_downloader import BilibiliDownloader
from pipeline.downloader.yt_dlp.yt_dlp_downloader import YtDlpDownloader

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

    async def download(self, url: str, output_dir: str, ctx: DownloaderContext) -> str or None:
        if not url.strip():
            logging.error("Url is empty")
            return None
        downloader = await get_downloader(url)
        if not downloader:
            logging.error("Downloader is None")
            return None
        return await downloader.download(url, output_dir, ctx)

    async def check(self, url: str) -> bool:
        if not url.strip():
            logging.error("Url is empty")
            return False
        downloader = await get_downloader(url)
        if not downloader:
            logging.error("Downloader is None")
            return False
        return await downloader.check(url)


pipeline = Pipeline()


async def main():
    url = "https://www.youtube.com/shorts/hjhkjhk"
    downloader = await get_downloader(url)
    if isinstance(downloader, YtDlpDownloader):
        print("YtDlpDownloader")
    if isinstance(downloader, BilibiliDownloader):
        print("BilibiliDownloader")


if __name__ == "__main__":
    asyncio.run(main())
