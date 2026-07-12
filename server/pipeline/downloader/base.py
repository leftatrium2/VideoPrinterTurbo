from abc import abstractmethod, ABC
from dataclasses import dataclass, field


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


class DownloaderContext(ABC):
    """
    Downloader context interface.
    Used to callback current download progress to the pipeline.
    """

    @abstractmethod
    async def on_create(self, url: str):
        pass

    @abstractmethod
    async def on_start(self, url: str):
        pass

    @abstractmethod
    async def on_progress(self, url: str, codec_type: int, progress: float):
        pass

    @abstractmethod
    async def on_error(self, url: str, error: Exception):
        pass

    @abstractmethod
    async def on_complete(self, url: str):
        pass


class BaseDownloader(ABC):
    """
    Base downloader class.
    """

    @abstractmethod
    async def download(self, url: str, output_dir: str, context: DownloaderContext) -> VideoPackage or None:
        pass

    @abstractmethod
    async def check(self, url: str) -> bool:
        pass
