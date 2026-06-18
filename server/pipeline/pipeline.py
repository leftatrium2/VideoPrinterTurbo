import logging

from pipeline.downloader.base import DownloadContext, BaseDownloader
from pipeline.downloader.bilibili.bilibili_downloader import BilibiliDownloader
from pipeline.downloader.yt_dlp.yt_dlp_downloader import YtDlpDownloader


def get_downloader(url: str) -> BaseDownloader or None:
    if not url:
        return None
    if url.find("bilibili"):
        downloader = BilibiliDownloader()
    else:
        downloader = YtDlpDownloader()
    return downloader


class Pipeline:
    def __init__(self):
        pass

    async def download(self, url: str, output_dir: str, ctx: DownloadContext) -> str or None:
        if not url.strip():
            logging.error("Url is empty")
            return None
        downloader = get_downloader(url)
        if not downloader:
            logging.error("Downloader is None")
            return None
        return downloader.download(url, output_dir, ctx)

    async def check(self, url: str) -> bool:
        if not url.strip():
            logging.error("Url is empty")
            return False
        downloader = get_downloader(url)
        if not downloader:
            logging.error("Downloader is None")
            return False
        return await downloader.check(url)


pipeline = Pipeline()
