from app.pipeline.downloader.base import DownloadContext
from app.pipeline.downloader.bilibili.bilibili_downloader import BilibiliDownloader
from app.pipeline.downloader.yt_dlp.yt_dlp_downloader import YtDlpDownloader


class Pipeline:
    def __init__(self):
        pass

    def download(self, url: str, output_dir: str, ctx: DownloadContext) -> str:
        if not url:
            return None
        if url.find("bilibili"):
            downloader = BilibiliDownloader()
        else:
            downloader = YtDlpDownloader()
        return downloader.download(url, output_dir, ctx)
