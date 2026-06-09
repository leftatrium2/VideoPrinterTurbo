"""PexelsSearcher — searches and downloads video footage from Pexels API."""

import os
import random
import threading
from typing import Optional
from urllib.parse import urlencode

import requests
from loguru import logger
from moviepy import VideoFileClip

from app.config import config
from app.models.schema import MaterialInfo, VideoAspect
from app.plugins.base import PluginType
from app.plugins.material.base import BaseMaterialSearcher
from app.utils import utils

_api_key_counter = 0
_api_key_lock = threading.Lock()


def _get_tls_verify() -> bool:
    verify = config.app.tls_verify
    if isinstance(verify, str):
        verify = verify.strip().lower() not in ("0", "false", "no", "off")
    return bool(verify)


def _get_api_key(cfg_key: str):
    keys = config.app.get(cfg_key)
    if not keys:
        raise ValueError(f"{cfg_key} is not set in config.toml")
    if isinstance(keys, str):
        return keys
    global _api_key_counter
    with _api_key_lock:
        _api_key_counter += 1
        return keys[_api_key_counter % len(keys)]


class PexelsSearcher(BaseMaterialSearcher):
    """Search and download videos from Pexels."""

    type = PluginType.MATERIAL
    name = "pexels"

    def validate_config(self) -> bool:
        return bool(config.app.get("pexels_api_keys"))

    def search(self, query: str, video_aspect=VideoAspect.portrait,
               min_duration: int = 5, per_page: int = 20) -> list[MaterialInfo]:
        aspect = VideoAspect(video_aspect) if isinstance(video_aspect, str) else video_aspect
        video_orientation = aspect.name
        video_width, video_height = aspect.to_resolution()

        api_key = _get_api_key("pexels_api_keys")
        headers = {"Authorization": api_key}
        params = {"query": query, "per_page": per_page, "orientation": video_orientation}
        url = f"https://api.pexels.com/videos/search?{urlencode(params)}"

        logger.info(f"searching pexels: {query}")
        try:
            r = requests.get(url, headers=headers, proxies=config.proxy,
                             verify=_get_tls_verify(), timeout=(30, 60))
            response = r.json()
        except Exception as e:
            logger.error(f"pexels search failed: {e}")
            return []

        items = []
        for v in response.get("videos", []):
            if v.get("duration", 0) < min_duration:
                continue
            for vf in v.get("video_files", []):
                if vf.get("width") == video_width and vf.get("height") == video_height:
                    items.append(MaterialInfo(
                        provider="pexels",
                        url=vf["link"],
                        duration=v["duration"],
                    ))
                    break
        return items

    def download(self, material: MaterialInfo, output_dir: str) -> str:
        if not output_dir:
            output_dir = utils.storage_dir("cache_videos", create=True)
        os.makedirs(output_dir, exist_ok=True)

        url_hash = utils.md5(material.url.split("?")[0])
        video_path = os.path.join(output_dir, f"vid-{url_hash}.mp4")

        if os.path.isfile(video_path) and os.path.getsize(video_path) > 0:
            return video_path

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        try:
            r = requests.get(material.url, headers=headers, proxies=config.proxy,
                             verify=_get_tls_verify(), timeout=(60, 240))
            with open(video_path, "wb") as f:
                f.write(r.content)
        except Exception as e:
            logger.error(f"download failed: {material.url}, error: {e}")
            return ""

        # Validate the downloaded file
        if os.path.isfile(video_path) and os.path.getsize(video_path) > 0:
            try:
                clip = VideoFileClip(video_path)
                duration = clip.duration
                clip.close()
                if duration > 0:
                    return video_path
            except Exception as e:
                logger.warning(f"invalid video: {video_path}, {e}")
                try:
                    os.remove(video_path)
                except OSError:
                    pass
        return ""
