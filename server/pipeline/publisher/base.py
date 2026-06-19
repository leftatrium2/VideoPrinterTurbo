from abc import abstractmethod, ABC
from typing import Optional


class BasePublisher(ABC):

    @abstractmethod
    def publish(self, video_path: str, title: str, description: str = "",
                tags: Optional[list[str]] = None) -> bool:
        pass
