"""YtDlpDownloader — downloads videos via yt-dlp with subtitle extraction."""
import asyncio
import os.path
import subprocess
from logging import info
from typing import Optional

import yt_dlp
from loguru import logger

from config.config import init_config
from pipeline.downloader.base import BaseDownloader, DownloaderContext, VideoBean
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

    def check(self, url: str, proxy: str = None) -> bool:
        yt_dlp_opts = {
            'quiet': True,
            'ignoreerrors': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True
        }
        if proxy:
            yt_dlp_opts['proxy'] = proxy
        with yt_dlp.YoutubeDL(yt_dlp_opts) as ydl:
            try:
                result = ydl.extract_info(url, download=False)
                if result['duration'] > 0:
                    return True
            except Exception as e:
                logger.error(e)
        return False

    def download(
            self,
            url: str,
            video_full_path: str,
            context: Optional[DownloaderContext],
            proxy: Optional[str]
    ) -> Optional[dict]:
        if context:
            context.on_create(url)
        yt_dlp_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            "outtmpl": f"{video_full_path}",
            "merge_output_format": "mp4",
            "quiet": True,
            'ignoreerrors': True,
            'no_warnings': True,
            "noprogress": True,
            "progress_hooks": [make_hook(context)],
        }
        if proxy:
            yt_dlp_opts['proxy'] = proxy
        ret_dict = {}
        ret_dict['url'] = url
        ret_dict['video_path'] = f"{video_full_path}.mp4"
        try:
            with yt_dlp.YoutubeDL(yt_dlp_opts) as ydl:
                # ydl.download([url])
                info = ydl.extract_info(
                    url=url,
                    download=True
                )
                ret_dict['title'] = info.get("title", "")
                ret_dict['duration'] = info.get("duration", 0.0)
                ret_dict['width'] = info.get("width", 0)
                ret_dict['height'] = info.get("height", 0)
                ret_dict['metadata'] = {
                    'uploader': info.get('uploader', ''),
                    'description': info.get('description', ''),
                    'thumbnail': info.get('thumbnail', ''),
                    'tags': info.get('tags', []),
                }
        except Exception as e:
            if context:
                context.on_error(url, e)
        return ret_dict


class TestDownloaderContext(DownloaderContext):
    def on_create(self, url: str):
        print(f"on_create: url: {url}")

    def on_start(self, url: str):
        print(f"on_start: url: {url}")

    def on_progress(self, url: str, codec_type: int, progress: float):
        print(f"on_progress: url: {url}, codec_type: {codec_type}, progress: {progress}")

    def on_error(self, url: str, error: Exception):
        print(f"on_error: url : {url}")
        print(error)

    def on_complete(self, url: str):
        print(f"on_complete: url: {url}")


if __name__ == "__main__":
    init_config()
    full_path = asyncio.run(get_download_path())
    full_path = os.path.join(full_path, "20260720215545133997")
    downloader = YtDlpDownloader()
    download_url = "https://www.youtube.com/watch?v=E7YiKBeOneo"
    proxy = "http://127.0.0.1:7890"
    if downloader.check(download_url):
        downloader.download(download_url, video_full_path=full_path, context=TestDownloaderContext(), proxy=proxy)
