import logging
from typing import List

from pipeline.transcriber.segment import Segment
from pipeline.transcriber.whisper_asr.engine.base_engine import BaseWhisperEngine

logger = logging.getLogger(__name__)


class OpenAIWhisperEngine(BaseWhisperEngine):
    """
    基于官方 openai-whisper 库的本地推理引擎。
    依赖 `pip install openai-whisper`（需要本机可用的 PyTorch 环境）。
    """

    def _load_model(self):
        try:
            import whisper
        except ImportError as e:
            raise ImportError(
                "未安装 openai-whisper，请先执行 `pip install openai-whisper`。"
            ) from e

        if self._model is None:
            logger.info(f"[OpenAIWhisperEngine] 加载模型: {self.model_size}")
            self._model = whisper.load_model(self.model_size)
        return self._model

    def run(self, audio_path: str) -> List[Segment]:
        model = self._load_model()
        result = model.transcribe(
            audio_path,
            language=self.language,
            **self.extra_kwargs,
        )

        segments = []
        for seg in result.get("segments", []):
            segments.append(
                Segment(start=float(seg["start"]), end=float(seg["end"]), text=seg["text"])
            )
        return segments
