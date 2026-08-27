import asyncio
import importlib
import logging
import os
from typing import Optional

from utils.file_utils import get_download_path
import config.config as _config
from pipeline.downloader.base import BaseDownloader, DownloaderContext, VideoBean
from pipeline.downloader.yt_dlp.yt_dlp_downloader import YtDlpDownloader


def init_downloader():
    """
    初始化下载器
    用来加载下载器插件
    """
    global downloaders
    for k, v in _config.downloader_config.items():
        v = v.strip()
        module_path, class_name = v.rsplit(".", 1)
        cls = getattr(importlib.import_module(module_path), class_name)
        downloaders[k] = cls()
    downloaders['others'] = YtDlpDownloader()


def check_video(
        url: str,
        proxy_url: Optional[str]
) -> bool:
    """
    检查视频是否可用
    """
    if not url.strip():
        logging.error("Url is empty")
        return False
    downloader = _get_downloader(url)
    if not downloader:
        logging.error("Downloader is None")
        return False
    return downloader.check(url, proxy_url)


def download_video(
        url: str,
        task_id: str,
        ctx: Optional[DownloaderContext],
        proxy_url: Optional[str]
) -> Optional[dict]:
    if not url.strip():
        logging.error("Url is empty")
        return None
    downloader = _get_downloader(url)
    if not downloader:
        logging.error("Downloader is None")
        return None
    video_full_path = asyncio.run(get_download_path())
    video_full_path = os.path.join(video_full_path, task_id)
    return downloader.download(url, video_full_path, ctx, proxy_url)


def _get_downloader(url: str) -> Optional[BaseDownloader]:
    """
    获取下载器，根据当前url中的域名部分，获取相应的下载器
    """
    if not url:
        return None
    for k, v in _config.downloader_config.items():
        keyword = k.lower().strip()
        if keyword in url:
            if k not in downloaders:
                logging.error("cant find the downloader, maybe it not init, keyword: ", k)
                return None
            return downloaders[k]

    return downloaders['others']


downloaders = {}
