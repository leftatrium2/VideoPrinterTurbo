from pipeline.downloader.base import BaseDownloader, DownloadContext, VideoPackage


class BilibiliDownloader(BaseDownloader):
    async def check(self, url: str) -> bool:
        return True

    async def download(self, url: str, output_dir: str, context: DownloadContext) -> VideoPackage or None:
        return None
