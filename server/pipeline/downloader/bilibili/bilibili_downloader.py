from app.pipeline.downloader.base import BaseDownloader, DownloadContext


class BilibiliDownloader(BaseDownloader):
    def download(self, url: str, output_dir: str, context: DownloadContext) -> str:
        return ""
