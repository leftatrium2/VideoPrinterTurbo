"""YtDlpDownloader — downloads videos via yt-dlp with subtitle extraction."""
import asyncio
import subprocess

import anyio
import yt_dlp
from loguru import logger

from pipeline.downloader.base import BaseDownloader, DownloaderContext, VideoPackage
from utils import const
from utils.const import DOWNLOADER_CODEC_VIDEO_TYPE, DOWNLOADER_CODEC_AUDIO_TYPE, DOWNLOADER_CODEC_MUXER_TYPE
from utils.exception import VPTException
from utils.file_utils import get_download_path


def make_hook(context: DownloaderContext):
    def hook(dict):
        match dict['status']:
            case 'downloading':
                progress = dict['downloaded_bytes'] / dict['total_bytes']
                info = dict.get('info_dict', {})
                vcodec = info.get("vcodec", "none")
                acodec = info.get("acodec", "none")
                if vcodec != "none" and acodec == "none":
                    stream_type = DOWNLOADER_CODEC_VIDEO_TYPE
                elif acodec != "none" and vcodec == "none":
                    stream_type = DOWNLOADER_CODEC_AUDIO_TYPE
                else:
                    stream_type = DOWNLOADER_CODEC_MUXER_TYPE
                context.on_progress(dict['info_dict']['original_url'], stream_type, progress)
                pass
            case 'finished':
                context.on_complete(dict['info_dict']['original_url'])
                pass
            case 'error':
                context.on_error(dict['info_dict']['original_url'], Exception(dict['err']))
                pass

    return hook


class YtDlpDownloader(BaseDownloader):
    def __init__(self):
        YtDlpDownloader._check_available()

    @staticmethod
    def _check_available():
        try:
            subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            logger.warning("yt-dlp not found. Install with: pip install yt-dlp")
            raise VPTException(code=const.GLOBAL_ERR_YT_DLP_NOT_INSTALLED,
                               message="yt-dlp not found. Install with: pip install yt-dlp")

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
                result = await anyio.to_thread.run_sync(lambda: ydl.extract_info(url, download=False))
                if result['duration'] > 0:
                    return True
            except Exception as e:
                logger.error(e)
        return False

    async def download(self, url: str, output_dir: str, context: DownloaderContext or None) -> VideoPackage or None:
        if context:
            context.on_create(url)
        yt_dlp_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
            "merge_output_format": "mp4",
            "quiet": True,
            'ignoreerrors': True,
            'no_warnings': True,
            "noprogress": True,
            "progress_hooks": [make_hook(context)],
        }
        try:
            with yt_dlp.YoutubeDL(yt_dlp_opts) as ydl:
                await anyio.to_thread.run_sync(lambda: ydl.download([url]))
        except Exception as e:
            if context:
                context.on_error(url, e)
        return None


async def __main():
    class YTDDownloadContext(DownloaderContext):
        def on_create(self, url: str):
            print("Creating download context for", url)

        def on_start(self, url: str):
            print("Starting download for", url)

        def on_progress(self, url: str, codec_type: int, progress: float):
            print("Download progress for", url, codec_type, progress)

        def on_error(self, url: str, error: Exception):
            print("Download error for", url, error)

        def on_complete(self, url: str):
            print("Completing download for", url)

    downloader = YtDlpDownloader()
    # asyncio.run(downloader.check('https://www.youtube.com/watch?v=WER937zS5sw'))
    # asyncio.run(downloader.check('https://www.youtube.com/watch?v=WER937zS5sd'))
    path = await get_download_path()
    await downloader.download('https://www.youtube.com/shorts/9OFFkNhVXnQ', path,
                              YTDDownloadContext())


if __name__ == "__main__":
    asyncio.run(__main())
