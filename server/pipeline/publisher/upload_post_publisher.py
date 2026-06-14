"""UploadPostPublisher — cross-post videos via upload-post.com API."""

import os
from typing import Optional

import requests
from loguru import logger

from app.config import config
from app.pipeline.base import PluginType
from app.pipeline.publisher.base import BasePublisher, PublishResult


class UploadPostPublisher(BasePublisher):
    """Publish videos to TikTok/Instagram via upload-post.com."""

    type = PluginType.PUBLISHER
    name = "upload_post"

    def validate_config(self) -> bool:
        return bool(config.app.upload_post_api_key and config.app.upload_post_username)

    def publish(self, video_path: str, title: str, description: str = "",
                tags: Optional[list[str]] = None) -> PublishResult:
        if not os.path.isfile(video_path):
            return PublishResult(success=False, platform="upload_post", error="video not found")

        api_key = config.app.upload_post_api_key
        username = config.app.upload_post_username
        platforms = config.app.upload_post_platforms

        if not api_key or not username:
            return PublishResult(success=False, platform="upload_post",
                                 error="upload_post not configured")

        url = "https://api.upload-post.com/v1/upload"
        headers = {"Authorization": f"Bearer {api_key}"}

        results = []
        for platform in platforms:
            try:
                with open(video_path, "rb") as f:
                    files = {"video": f}
                    data = {
                        "username": username,
                        "platform": platform,
                        "title": title[:150],
                        "description": description[:500] or title[:500],
                    }
                    r = requests.post(url, headers=headers, files=files, data=data, timeout=(60, 300))
                    if r.status_code == 200:
                        result_data = r.json()
                        results.append(PublishResult(
                            success=True,
                            platform=platform,
                            url=result_data.get("url", ""),
                        ))
                        logger.success(f"published to {platform}: {result_data.get('url', '')}")
                    else:
                        results.append(PublishResult(
                            success=False,
                            platform=platform,
                            error=f"HTTP {r.status_code}: {r.text[:200]}",
                        ))
                        logger.warning(f"publish to {platform} failed: {r.status_code}")
            except Exception as e:
                results.append(PublishResult(success=False, platform=platform, error=str(e)))
                logger.error(f"publish to {platform} error: {e}")

        # Return first result as summary
        if results:
            return results[0]
        return PublishResult(success=False, platform="upload_post", error="no platforms configured")
