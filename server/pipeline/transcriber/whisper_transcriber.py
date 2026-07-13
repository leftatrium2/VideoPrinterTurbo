from pipeline.transcriber.base import BaseTranscriber


class WhisperTranscriber(BaseTranscriber):

    def transcribe(self, audio_path: str) -> str or None:
        return None
