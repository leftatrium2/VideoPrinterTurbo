from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from typing import Optional

from utils.const import PIPELINE_STATUS_INIT


@dataclass
class VideoBean:
    """Standardised output from a downloader."""
    video_path: str = ""
    audio_path: str = ""
    subtitle_path: str = ""
    metadata: dict = field(default_factory=dict)
    title: str = ""
    duration: float = 0.0
    width: int = 0
    height: int = 0


@dataclass
class AsrBean:
    pass


@dataclass
class LLMBean:
    pass


@dataclass
class TTSBean:
    pass


@dataclass
class SubtitleBean:
    pass


@dataclass
class BGMBean:
    pass


@dataclass
class PipeLineData:
    task_id: str = ""
    url: str = ""
    status: int = PIPELINE_STATUS_INIT
    video_bean: VideoBean = None
    asr_bean: AsrBean = None
    llm_bean: LLMBean = None
    tts_bean: TTSBean = None
    subtitle_bean: SubtitleBean = None
    bgm_bean: BGMBean = None


class DownloaderContext(ABC):
    """
    Downloader context interface.
    Used to callback current download progress to the pipeline.
    """

    @abstractmethod
    def on_create(self, url: str):
        pass

    @abstractmethod
    def on_start(self, url: str):
        pass

    @abstractmethod
    def on_progress(self, url: str, codec_type: int, progress: float):
        pass

    @abstractmethod
    def on_error(self, url: str, error: Exception):
        pass

    @abstractmethod
    def on_complete(self, url: str):
        pass


class BaseDownloader(ABC):
    """
    Base downloader class.
    """

    @abstractmethod
    def download(
            self,
            url: str,
            video_full_path: str,
            context: Optional[DownloaderContext],
            proxy: str = None
    ) -> Optional[VideoBean]:
        """
        :param video_full_path: 不包含扩展名的视频存储地址
        """
        pass

    @abstractmethod
    def check(
            self,
            url: str,
            proxy: str = None
    ) -> bool:
        pass
