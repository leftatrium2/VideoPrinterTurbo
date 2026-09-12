from abc import abstractmethod, ABC
from typing import Optional


# ASR 功能，本身不带翻译功能
class BaseTranscriber(ABC):
    @abstractmethod
    def config(self, proxy: Optional[str] = None):
        pass

    # Transcribe audio file into text segments with timestamps
    @abstractmethod
    def transcribe(self, audio_path: str) -> Optional[str]:
        pass
