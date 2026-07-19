from abc import ABC, abstractmethod
from typing import List

from pipeline.transcriber.segment import Segment


class BaseWhisperEngine(ABC):
    def __init__(self, model_size: str = "large-v3", language: str = None, **kwargs):
        self.model_size = model_size
        self.language = language
        self.extra_kwargs = kwargs
        self._model = None  # 惰性加载

    @abstractmethod
    def run(self, audio_path: str) -> List[Segment]:
        pass
