"""YtDlpDownloader — downloads videos via yt-dlp with subtitle extraction."""

import subprocess

from loguru import logger

from pipeline.downloader.base import BaseDownloader, DownloadContext, VideoPackage
from utils import const
from utils.exception import VPTException


class YtDlpDownloader(BaseDownloader):
    """Download videos from URLs using yt-dlp.

    Supports automatic subtitle extraction and audio extraction.
    """

    name = "yt-dlp"

    def __init__(self):
        self._check_available()

    async def check(self, url: str) -> bool:
        
        return True

    @staticmethod
    def _check_available():
        try:
            subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            logger.warning("yt-dlp not found. Install with: pip install yt-dlp")
            raise VPTException(code=const.GLOBAL_ERR_YT_DLP_NOT_INSTALLED,
                               message="yt-dlp not found. Install with: pip install yt-dlp")

    async def download(self, url: str, output_dir: str, context: DownloadContext) -> VideoPackage or None:
        return None
