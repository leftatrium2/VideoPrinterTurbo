"""YtDlpDownloader — downloads videos via yt-dlp with subtitle extraction."""
import asyncio
import os.path
import subprocess
from typing import Optional

import yt_dlp
from loguru import logger

from config.config import init_config
from pipeline.downloader.base import BaseDownloader, DownloaderContext
from utils import const
from utils.const import DOWNLOADER_CODEC_VIDEO_TYPE, DOWNLOADER_CODEC_AUDIO_TYPE, DOWNLOADER_CODEC_MUXER_TYPE
from utils.exception import VPTException
from utils.file_utils import get_download_path


def make_hook(context: DownloaderContext):
    def hook(progress):
        status = progress.get('status')
        info = progress.get('info_dict') or {}
        original_url = info.get('original_url', '')
        match status:
            case 'downloading':
                downloaded = progress.get('downloaded_bytes', 0) or 0
                total = progress.get('total_bytes') or progress.get('total_bytes_estimate') or 0
                progress_ratio = downloaded / total if total > 0 else 0.0
                vcodec = info.get("vcodec", "none")
                acodec = info.get("acodec", "none")
                if vcodec != "none" and acodec == "none":
                    stream_type = DOWNLOADER_CODEC_VIDEO_TYPE
                elif acodec != "none" and vcodec == "none":
                    stream_type = DOWNLOADER_CODEC_AUDIO_TYPE
                else:
                    stream_type = DOWNLOADER_CODEC_MUXER_TYPE
                context.on_progress(original_url, stream_type, progress_ratio)
            case 'finished':
                context.on_complete(original_url)
            case 'error':
                context.on_error(original_url, Exception(progress.get('err', 'yt-dlp error')))

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

    def check(
            self,
            url: str,
            proxy_type: int = const.PROXY_CONFIG_TYPE_UNKNOWN,
            proxy_url: Optional[str] = None
    ) -> bool:
        yt_dlp_opts = {
            'quiet': True,
            'ignoreerrors': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True
        }
        if proxy_url:
            # socks5h:// — DNS 交给代理服务器解析，对于翻墙场景更可靠
            if proxy_url.startswith("socks5://"):
                proxy_url = proxy_url.replace("socks5://", "socks5h://", 1)
            yt_dlp_opts['proxy'] = proxy_url
        with yt_dlp.YoutubeDL(yt_dlp_opts) as ydl:  # type: ignore[arg-type]
            try:
                result = ydl.extract_info(url, download=False)
                if result and result.get('duration', 0) > 0:
                    return True
            except Exception as e:
                raise VPTException(const.PIPELINE_ERR_YT_DLP, str(e), tr=e) from e
        return False

    def download(
            self,
            url: str,
            video_full_path: str,
            context: Optional[DownloaderContext] = None,
            proxy_type: int = const.PROXY_CONFIG_TYPE_UNKNOWN,
            proxy_url: Optional[str] = None
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
        }
        if context:
            yt_dlp_opts["progress_hooks"] = [make_hook(context)]
        if proxy_url:
            if proxy_url.startswith("socks5://"):
                proxy_url = proxy_url.replace("socks5://", "socks5h://", 1)
            yt_dlp_opts['proxy'] = proxy_url
        ret_dict = {}
        ret_dict['url'] = url
        try:
            with yt_dlp.YoutubeDL(yt_dlp_opts) as ydl:  # type: ignore[arg-type]
                # ydl.download([url])
                info = ydl.extract_info(
                    url=url,
                    download=True
                ) or {}
                ret_dict['video_path'] = f"{video_full_path}.mp4"
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
                ret_dict['status'] = 0
                ret_dict['message'] = ""
        except Exception as e:
            if context:
                context.on_error(url, e)
            raise VPTException(const.PIPELINE_ERR_YT_DLP, str(e), tr=e) from e
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
    if downloader.check(download_url, proxy_type=const.PROXY_CONFIG_TYPE_HTTPS, proxy_url=proxy):
        downloader.download(download_url, video_full_path=full_path, context=TestDownloaderContext(),
                            proxy_type=const.PROXY_CONFIG_TYPE_HTTPS, proxy_url=proxy)
