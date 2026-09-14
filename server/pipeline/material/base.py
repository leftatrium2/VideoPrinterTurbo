from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


@dataclass(frozen=True)
class MaterialInfo:
    """A downloadable video returned by a material provider."""

    provider: str
    url: str
    keyword: str
    duration: int


class VideoAspect(Enum):
    portrait = 1
    landscape = 2

    def to_resolution(self) -> tuple[int, int]:
        """Return the minimum Full-HD target resolution for this aspect."""
        if self is VideoAspect.portrait:
            return 1080, 1920
        return 1920, 1080

    @classmethod
    def coerce(cls, value: "VideoAspect | str | int") -> "VideoAspect":
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls[value.lower()]
        return cls(value)


class BaseMaterialSearcher(ABC):
    """Provider-independent contract for video material search and download."""

    @abstractmethod
    def config(
            self,
            proxy_url: Optional[str] = None,
            api_keys: str | list[str] | tuple[str, ...] | None = None,
            tls_verify: bool = True,
    ):
        """Configure the provider client before calling :meth:`search`."""

    @abstractmethod
    def search(
            self,
            query: list[str],
            video_aspect: VideoAspect = VideoAspect.portrait,
            min_duration: int = 5,
            per_page: int = 30,
    ) -> list[MaterialInfo]:
        """Search the provider and return directly downloadable videos."""

    @abstractmethod
    def download(self, material: MaterialInfo, output_dir: str) -> str:
        """Download ``material`` into ``output_dir`` and return its local path."""
