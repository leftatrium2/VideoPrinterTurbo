from pipeline.transcriber.base import BaseTranscriber


class XFCloudASR(BaseTranscriber):
    def transcribe(self, audio_path: str) -> str or None:
        return None
