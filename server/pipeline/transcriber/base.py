from abc import abstractmethod, ABC
from typing import Optional


class BaseTranscriber(ABC):

    # 将音频文件转写为带时间轴的文本片段
    @abstractmethod
    def transcribe(self, audio_path: str, language: Optional[str] = None) -> list:
        pass

    # 视频文件中提取字幕
    # video_path：本地视频文件路径
    @abstractmethod
    def extract_subtitles(self, video_path: str) -> list:
        pass
