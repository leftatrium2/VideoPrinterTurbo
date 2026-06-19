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
    下载器的上下文接口
    用来将当前下载的状态回调到pipeline里面
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
    下载器基类
    """

    @abstractmethod
    async def download(self, url: str, output_dir: str, context: DownloaderContext) -> VideoPackage:
        pass

    @abstractmethod
    async def check(self, url: str) -> bool:
        pass
