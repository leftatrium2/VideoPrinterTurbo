from typing import Optional

from pipeline.transcriber.base import BaseTranscriber


class TencentCloudTranscriber(BaseTranscriber):
    def transcribe(self, audio_path: str, language: Optional[str] = None) -> list:
        pass

    def extract_subtitles(self, video_path: str) -> list:
        pass
