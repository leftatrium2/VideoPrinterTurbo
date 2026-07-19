"""PixabaySearcher — searches and downloads video footage from Pixabay API."""

import os
from urllib.parse import urlencode

import requests
from loguru import logger
from moviepy import VideoFileClip

from pipeline.material.base import BaseMaterialSearcher, VideoAspect, MaterialInfo


class PixabaySearcher(BaseMaterialSearcher):

    def validate_config(self) -> bool:
        return bool("pixabay_api_keys")

    def search(self, query: str, video_aspect=VideoAspect.portrait,
               min_duration: int = 5, per_page: int = 50) -> list[MaterialInfo]:
        aspect = VideoAspect(video_aspect) if isinstance(video_aspect, str) else video_aspect
        video_width, _ = aspect.to_resolution()

        api_key = _get_api_key("pixabay_api_keys")
        params = {"q": query, "video_type": "all", "per_page": per_page, "key": api_key}
        url = f"https://pixabay.com/api/videos/?{urlencode(params)}"

        logger.info(f"searching pixabay: {query}")
        try:
            r = requests.get(url, proxies=config.proxies, verify=_get_tls_verify(), timeout=(30, 60))
            response = r.json()
        except Exception as e:
            logger.error(f"pixabay search failed: {e}")
            return []

        items = []
        for v in response.get("hits", []):
            if v.get("duration", 0) < min_duration:
                continue
            for video_type, video in v.get("videos", {}).items():
                w = int(video.get("width", 0))
                if w >= video_width:
                    items.append(MaterialInfo(
                        provider="pixabay",
                        url=video["url"],
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
            r = requests.get(material.url, headers=headers, proxies=config.proxies,
                             verify=_get_tls_verify(), timeout=(60, 240))
            with open(video_path, "wb") as f:
                f.write(r.content)
        except Exception as e:
            logger.error(f"download failed: {material.url}, error: {e}")
            return ""

        if os.path.isfile(video_path) and os.path.getsize(video_path) > 0:
            try:
                clip = VideoFileClip(video_path)
                duration = clip.duration
                clip.close()
                if duration > 0:
                    return video_path
            except Exception:
                try:
                    os.remove(video_path)
                except OSError:
                    pass
        return ""
