from abc import abstractmethod
from typing import Optional

from app.models.schema import TranscriptSegment
from app.pipeline.base import BasePlugin, PluginType


class BaseTranscriber(BasePlugin):
    """
    将音频 / 视频转换为带时间轴的文本片段
    基类，不要直接调用
    """
    type = PluginType.TRANSCRIBER

    # 将音频文件转写为带时间轴的文本片段
    @abstractmethod
    def transcribe(self, audio_path: str, language: Optional[str] = None) -> list[TranscriptSegment]:
        ...

    # 视频文件中提取字幕
    # video_path：本地视频文件路径
    @abstractmethod
    def extract_subtitles(self, video_path: str) -> list[TranscriptSegment]:
        ...
