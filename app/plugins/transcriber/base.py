"""BaseTranscriber — abstract interface for audio transcription / subtitle extraction."""

from abc import abstractmethod
from typing import Optional

from app.models.schema import TranscriptSegment
from app.plugins.base import BasePlugin, PluginType


class BaseTranscriber(BasePlugin):
    """Convert audio or video to timed text segments."""

    type = PluginType.TRANSCRIBER

    @abstractmethod
    def transcribe(self, audio_path: str, language: Optional[str] = None) -> list[TranscriptSegment]:
        """Transcribe an audio file into text segments with timing.

        Args:
            audio_path: Path to the audio file.
            language: Optional language code hint (e.g. "zh", "en").

        Returns:
            List of TranscriptSegment with text + start/end times.

        Raises:
            RuntimeError: If transcription fails.
        """
        ...

    @abstractmethod
    def extract_subtitles(self, video_path: str) -> list[TranscriptSegment]:
        """Extract embedded subtitles from a video file.

        Args:
            video_path: Path to the video file.

        Returns:
            List of TranscriptSegment, or empty list if no subtitles found.
        """
        ...
