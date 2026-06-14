from abc import abstractmethod, ABC
from dataclasses import dataclass, field

from app.pipeline.base import BasePlugin, PluginType


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


class DownloadContext(ABC):
    """
    下载器的上下文接口
    用来将当前下载的状态回调到pipeline里面
    """

    @abstractmethod
    def on_create(self, url: str):
        pass

    @abstractmethod
    def on_start(self, url: str):
        pass

    @abstractmethod
    def on_progress(self, url: str, progress: float):
        pass

    @abstractmethod
    def on_error(self, url: str, error: Exception):
        pass

    @abstractmethod
    def on_complete(self, url: str):
        pass


class BaseDownloader(BasePlugin):
    """
    下载器基类
    """

    @abstractmethod
    def download(self, url: str, output_dir: str, context: DownloadContext) -> VideoPackage:
        pass
