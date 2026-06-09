"""BasePublisher — abstract interface for social media publishing plugins."""

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from app.plugins.base import BasePlugin, PluginType


@dataclass
class PublishResult:
    """Result of a publish operation."""
    success: bool = False
    platform: str = ""
    url: str = ""
    error: str = ""


class BasePublisher(BasePlugin):
    """Publish a video to a social media platform."""

    type = PluginType.PUBLISHER

    @abstractmethod
    def publish(self, video_path: str, title: str, description: str = "",
                tags: Optional[list[str]] = None) -> PublishResult:
        """Publish a video to the platform.

        Args:
            video_path: Local path to the video file.
            title: Video title.
            description: Video description.
            tags: Optional list of tags.

        Returns:
            PublishResult with success status and platform URL.
        """
        ...
