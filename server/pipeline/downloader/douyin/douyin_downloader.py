from pipeline.downloader.base import BaseDownloader, DownloaderContext, VideoPackage


class DouyinDownloader(BaseDownloader):
    def check(self, url: str, proxy: str = None) -> bool:
        return True

    def download(self, url: str, output_dir: str, context: DownloaderContext,
                 proxy: str = None) -> VideoPackage or None:
        return None
