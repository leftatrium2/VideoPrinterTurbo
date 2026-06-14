"""BaseMaterialSearcher — abstract interface for video/image material search plugins."""

from abc import abstractmethod
from typing import Optional

from app.models.schema import MaterialInfo, VideoAspect
from app.pipeline.base import BasePlugin, PluginType


class BaseMaterialSearcher(BasePlugin):
    """Search for video/image footage from external providers."""

    type = PluginType.MATERIAL

    @abstractmethod
    def search(self, query: str, video_aspect: VideoAspect = VideoAspect.portrait,
               min_duration: int = 5, per_page: int = 20) -> list[MaterialInfo]:
        """Search for video materials matching the query.

        Args:
            query: Search keywords.
            video_aspect: Desired aspect ratio.
            min_duration: Minimum clip duration in seconds.
            per_page: Results per page.

        Returns:
            List of MaterialInfo with provider, URL, and duration.
        """
        ...

    @abstractmethod
    def download(self, material: MaterialInfo, output_dir: str) -> str:
        """Download a material to the local filesystem.

        Args:
            material: The material to download.
            output_dir: Directory to save to.

        Returns:
            Local file path of the downloaded material, or empty string on failure.
        """
        ...
