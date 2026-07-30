"""Search and download video footage from the Pixabay API."""
import asyncio
import hashlib
import os
from pathlib import Path
from urllib.parse import urlsplit

import requests
from loguru import logger
from moviepy import VideoFileClip

from config.config import init_config
from pipeline.material.base import BaseMaterialSearcher, MaterialInfo, VideoAspect
from utils.file_utils import get_material_path


class PixabaySearcher(BaseMaterialSearcher):
    _SEARCH_URL = "https://pixabay.com/api/videos/"

    def __init__(self) -> None:
        self._api_keys: list[str] = []
        self._api_key_index = 0
        self._proxies: dict[str, str] | None = None
        self._tls_verify = True

    def config(self, proxy=None, api_keys=None, tls_verify=True) -> None:
        if isinstance(api_keys, str):
            api_keys = [api_keys]
        self._api_keys = [key.strip() for key in (api_keys or []) if key and key.strip()]
        self._api_key_index = 0
        self._proxies = {"http": proxy, "https": proxy} if proxy else None
        self._tls_verify = bool(tls_verify)

    def validate_config(self) -> bool:
        return bool(self._api_keys)

    def _next_api_key(self) -> str | None:
        if not self._api_keys:
            return None
        key = self._api_keys[self._api_key_index % len(self._api_keys)]
        self._api_key_index += 1
        return key

    def search(self, query, video_aspect=VideoAspect.portrait, min_duration=5, per_page=20):
        if not query or not self.validate_config():
            logger.warning("Pixabay search skipped: query or API key is missing")
            return []
        try:
            aspect = VideoAspect.coerce(video_aspect)
        except (KeyError, ValueError):
            logger.warning("Pixabay search skipped: unsupported video aspect {}", video_aspect)
            return []

        target_width, target_height = aspect.to_resolution()
        params = {
            "key": self._next_api_key(),
            "q": query,
            "video_type": "all",
            "per_page": max(3, min(int(per_page), 200)),
            "min_width": target_width,
            "min_height": target_height,
        }
        try:
            response = requests.get(
                self._SEARCH_URL,
                params=params,
                proxies=self._proxies,
                verify=self._tls_verify,
                timeout=(30, 60),
            )
            response.raise_for_status()
            videos = response.json().get("hits", [])
        except (requests.RequestException, ValueError) as exc:
            logger.error("Pixabay search failed for {!r}: {}", query, exc)
            return []

        items = []
        for video in videos:
            if int(video.get("duration") or 0) < min_duration:
                continue
            file_info = self._select_file(video.get("videos") or {}, aspect)
            if file_info:
                items.append(MaterialInfo("pixabay", file_info["url"], int(video["duration"])))
        return items

    @staticmethod
    def _select_file(files, aspect):
        matching = [
            item for item in files.values()
            if item.get("url")
               and ((item.get("height", 0) > item.get("width", 0)) == (aspect is VideoAspect.portrait))
        ]
        return max(matching, key=lambda item: item.get("width", 0) * item.get("height", 0), default=None)

    def download(self, material, output_dir):
        if material.provider != "pixabay" or not material.url or not output_dir:
            return ""
        return self._download(material.url, output_dir)

    def _download(self, url, output_dir):
        filename = f"pixabay-{hashlib.sha256(urlsplit(url).path.encode()).hexdigest()}.mp4"
        video_path = Path(output_dir) / filename
        temporary_path = video_path.with_suffix(".part")
        try:
            video_path.parent.mkdir(parents=True, exist_ok=True)
            if video_path.is_file() and video_path.stat().st_size > 0:
                return str(video_path)
            with requests.get(
                    url,
                    headers={"User-Agent": "VideoPrinterTurbo/1.0"},
                    proxies=self._proxies,
                    verify=self._tls_verify,
                    timeout=(60, 240),
                    stream=True,
            ) as response:
                response.raise_for_status()
                with temporary_path.open("wb") as file:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            file.write(chunk)
            if not self._is_valid_video(temporary_path):
                temporary_path.unlink(missing_ok=True)
                return ""
            os.replace(temporary_path, video_path)
            return str(video_path)
        except (OSError, requests.RequestException) as exc:
            logger.error("Pixabay download failed for {}: {}", url, exc)
            temporary_path.unlink(missing_ok=True)
            return ""

    @staticmethod
    def _is_valid_video(path):
        try:
            with VideoFileClip(str(path)) as clip:
                return bool(clip.duration and clip.duration > 0)
        except Exception as exc:
            logger.warning("Downloaded Pixabay video is invalid: {}", exc)
            return False

