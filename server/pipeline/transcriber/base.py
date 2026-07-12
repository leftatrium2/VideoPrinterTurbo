from abc import abstractmethod, ABC
from typing import Optional


class BaseTranscriber(ABC):

    # Transcribe audio file into text segments with timestamps
    @abstractmethod
    def transcribe(self, audio_path: str, language: Optional[str] = None) -> list:
        pass

    # Extract subtitles from video file
    # video_path: local video file path
    @abstractmethod
    def extract_subtitles(self, video_path: str) -> list:
        pass
