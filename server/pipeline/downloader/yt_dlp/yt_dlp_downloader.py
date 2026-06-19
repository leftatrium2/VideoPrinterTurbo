"""YtDlpDownloader — downloads videos via yt-dlp with subtitle extraction."""
import asyncio
import json
import subprocess

from loguru import logger

from pipeline.downloader.base import BaseDownloader, DownloadContext, VideoPackage
from utils import const
from utils.exception import VPTException
import yt_dlp


class YtDlpDownloader(BaseDownloader):
    def __init__(self):
        self._check_available()

    async def check(self, url: str) -> bool:
        yt_dlp_opts = {
            'quiet': True,
            'ignoreerrors': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True
        }
        with yt_dlp.YoutubeDL(yt_dlp_opts) as ydl:
            try:
                result = ydl.extract_info(url, download=False)
                if result['duration'] > 0:
                    return True
            except Exception as e:
                logger.error(e)
        return False

    @staticmethod
    def _check_available():
        try:
            subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            logger.warning("yt-dlp not found. Install with: pip install yt-dlp")
            raise VPTException(code=const.GLOBAL_ERR_YT_DLP_NOT_INSTALLED,
                               message="yt-dlp not found. Install with: pip install yt-dlp")

    async def download(self, url: str, output_dir: str, context: DownloadContext) -> VideoPackage or None:
        yt_dlp_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        }
        try:
            with yt_dlp.YoutubeDL(yt_dlp_opts) as ydl:
                result = ydl.download([url])
        except Exception as e:
            print(e)
        return None


if __name__ == "__main__":
    downloader = YtDlpDownloader()
    asyncio.run(downloader.check('https://www.youtube.com/watch?v=WER937zS5sw'))
    # asyncio.run(downloader.check('https://www.youtube.com/watch?v=WER937zS5sd'))
