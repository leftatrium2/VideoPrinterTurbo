from dataclasses import dataclass
from abc import abstractmethod, ABC
from enum import Enum


@dataclass
class MaterialInfo:
    provider: str
    url: str
    duration: int
    pass


class VideoAspect(Enum):
    portrait = 1
    landscape = 2


class BaseMaterialSearcher(ABC):

    @abstractmethod
    def search(self, query: str, video_aspect: VideoAspect = VideoAspect.portrait,
               min_duration: int = 5, per_page: int = 20) -> list[MaterialInfo]:
        pass

    @abstractmethod
    def download(self, material: MaterialInfo, output_dir: str) -> str:
        pass
