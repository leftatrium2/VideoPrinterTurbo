from abc import abstractmethod, ABC
from typing import Optional


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
            proxy: Optional[str]
    ) -> Optional[dict]:
        """
        Download video from given url.
        """
        pass

    @abstractmethod
    def check(
            self,
            url: str,
            proxy: Optional[str]
    ) -> bool:
        """
        check video url is valid.
        """
        pass
