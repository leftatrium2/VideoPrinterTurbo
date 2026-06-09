"""BaseDownloader — abstract interface for video download plugins."""

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from app.plugins.base import BasePlugin, PluginType


@dataclass
class VideoPackage:
    """Standardised output from a downloader."""
    video_path: str = ""
    audio_path: str = ""
    subtitle_path: str = ""
    metadata: dict = field(default_factory=dict)
    title: str = ""
    duration: float = 0.0
    width: int = 0
    height: int = 0


class BaseDownloader(BasePlugin):
    """Download a video from a URL and return a VideoPackage."""

    type = PluginType.DOWNLOADER

    @abstractmethod
    def download(self, url: str, output_dir: str = "") -> VideoPackage:
        """Download the video at ``url`` and return local file paths.

        Args:
            url: The video URL to download.
            output_dir: Optional override for the download directory.

        Returns:
            VideoPackage with paths to the downloaded video, audio, and optional subtitle.

        Raises:
            RuntimeError: If the download fails.
        """
        ...
