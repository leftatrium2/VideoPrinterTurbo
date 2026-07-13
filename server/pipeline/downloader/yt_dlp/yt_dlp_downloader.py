"""YtDlpDownloader — downloads videos via yt-dlp with subtitle extraction."""
import subprocess

import yt_dlp
from loguru import logger

from pipeline.downloader.base import BaseDownloader, DownloaderContext, VideoPackage
from utils import const
from utils.const import DOWNLOADER_CODEC_VIDEO_TYPE, DOWNLOADER_CODEC_AUDIO_TYPE, DOWNLOADER_CODEC_MUXER_TYPE
from utils.exception import VPTException


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

    def download(self, url: str, output_dir: str, context: DownloaderContext or None,
                 proxy: str = None) -> VideoPackage or None:
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
        if proxy:
            yt_dlp_opts['proxy'] = proxy
        try:
            with yt_dlp.YoutubeDL(yt_dlp_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            if context:
                context.on_error(url, e)
        return None
