import asyncio
import importlib
import json
import logging
import os
from typing import Optional

import config.config as _config
from pipeline.downloader.base import DownloaderContext, BaseDownloader
from pipeline.downloader.yt_dlp.yt_dlp_downloader import YtDlpDownloader
from utils import const
from utils.exception import VPTException
from utils.file_utils import get_download_path

logger = logging.getLogger(__name__)


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
        proxy_type: int = const.PROXY_CONFIG_TYPE_UNKNOWN,
        proxy_url: Optional[str] = None
) -> bool:
    """
    检查视频是否可用
    """
    if not url.strip():
        raise VPTException(const.PIPELINE_ERR_VALUE, "Url is empty")
    downloader = _get_downloader(url)
    if not downloader:
        raise VPTException(const.PIPELINE_ERR_DOWNLOADER_NONE, "Downloader is None")
    return downloader.check(url, proxy_type=proxy_type, proxy_url=proxy_url)


def download_video(
        url: str,
        task_id: str,
        ctx: Optional[DownloaderContext] = None,
        proxy_type: int = const.PROXY_CONFIG_TYPE_UNKNOWN,
        proxy_url: Optional[str] = None
) -> Optional[dict]:
    if not url.strip():
        logger.error("Url is empty")
        return None
    downloader = _get_downloader(url)
    if not downloader:
        logger.error("Downloader is None")
        return None
    video_full_path = asyncio.run(get_download_path())
    video_full_path = os.path.join(video_full_path, task_id)
    return downloader.download(url, video_full_path, context=ctx, proxy_type=proxy_type, proxy_url=proxy_url)


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
                logger.error("cant find the downloader, maybe it not init, keyword: ", k)
                return None
            return downloaders[k]

    return downloaders['others']


downloaders = {}

if __name__ == "__main__":
    _config.init_config()
    init_downloader()
    result = download_video(
        url="https://www.youtube.com/watch?v=FwOTs4UxQS4",
        task_id="20260720215545133997",
        ctx=None,
        proxy_url="http://127.0.0.1:7890"
    )
    print(f"{json.dumps(result)}")
