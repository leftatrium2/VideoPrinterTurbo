"""WhisperTranscriber — ASR transcription using faster-whisper."""

import os
from typing import Optional

from loguru import logger

from app.config import config
from app.models.schema import TranscriptSegment
from app.pipeline.base import PluginType
from app.pipeline.transcriber.base import BaseTranscriber
from app.utils import utils


class WhisperTranscriber(BaseTranscriber):
    """Transcribe audio to text using faster-whisper.

    Supports CPU and GPU inference. Model is loaded on first use.
    """

    type = PluginType.TRANSCRIBER
    name = "whisper"

    def __init__(self):
        self._model = None
        self._model_path = ""

    def validate_config(self) -> bool:
        return True

    def _load_model(self):
        if self._model is not None:
            return

        try:
            from faster_whisper import WhisperModel
        except ImportError:
            logger.error("faster-whisper not installed. Run: uv sync")
            raise RuntimeError("faster-whisper not available")

        model_size = config.whisper.model_size
        device = config.whisper.device
        compute_type = config.whisper.compute_type

        # Check for local model file
        model_path = os.path.join(utils.root_dir(), "models", f"whisper-{model_size}")
        model_bin = os.path.join(model_path, "model.bin")
        if os.path.isdir(model_path) and os.path.isfile(model_bin):
            self._model_path = model_path
        else:
            self._model_path = model_size

        logger.info(f"loading whisper model: {self._model_path}, device: {device}, compute_type: {compute_type}")
        self._model = WhisperModel(self._model_path, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> list[TranscriptSegment]:
        """Transcribe audio to text segments."""
        if not audio_path or not os.path.isfile(audio_path):
            logger.error(f"audio file not found: {audio_path}")
            return []

        self._load_model()

        segments, info = self._model.transcribe(
            audio_path,
            beam_size=5,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
            language=language,
        )

        logger.info(f"detected language: '{info.language}', probability: {info.language_probability:.2f}")

        result = []
        for i, seg in enumerate(segments, 1):
            text = seg.text.strip()
            if text:
                result.append(TranscriptSegment(index=i, text=text, start=seg.start, end=seg.end))

        return result

    def extract_subtitles(self, video_path: str) -> list[TranscriptSegment]:
        """Extract subtitles — falls back to transcribing the audio track.

        For WhisperTranscriber, this extracts audio from the video and transcribes it.
        """
        if not video_path or not os.path.isfile(video_path):
            return []

        # Extract audio from video
        import subprocess
        audio_path = video_path + ".tmp_audio.wav"
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le",
                 "-ar", "16000", "-ac", "1", audio_path],
                capture_output=True, check=True, timeout=120,
            )
            return self.transcribe(audio_path)
        except Exception as e:
            logger.error(f"failed to extract audio for transcription: {e}")
            return []
        finally:
            if os.path.isfile(audio_path):
                try:
                    os.remove(audio_path)
                except OSError:
                    pass
