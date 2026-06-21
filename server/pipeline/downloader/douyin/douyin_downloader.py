from pipeline.downloader.base import BaseDownloader, DownloaderContext, VideoPackage


class DouyinDownloader(BaseDownloader):
    async def check(self, url: str) -> bool:
        return True

    async def download(self, url: str, output_dir: str, context: DownloaderContext) -> VideoPackage or None:
        return None
