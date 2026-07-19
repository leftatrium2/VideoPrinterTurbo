import logging
from typing import List

from pipeline.transcriber.segment import Segment
from pipeline.transcriber.whisper_asr.engine.base_engine import BaseWhisperEngine

logger = logging.getLogger(__name__)


class FasterWhisperEngine(BaseWhisperEngine):
    """
    基于 faster-whisper（CTranslate2 实现）的本地推理引擎。
    依赖 `pip install faster-whisper`。
    """

    def __init__(
            self,
            model_size: str = "large-v3",
            language: str = None,
            device: str = "auto",
            compute_type: str = "default",
            **kwargs,
    ):
        super().__init__(model_size=model_size, language=language, **kwargs)
        self.device = device
        self.compute_type = compute_type

    def _load_model(self):
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise ImportError(
                "未安装 faster-whisper，请先执行 `pip install faster-whisper`。"
            ) from e

        if self._model is None:
            logger.info(f"[FasterWhisperEngine] 加载模型: {self.model_size} (device={self.device})")
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
        return self._model

    def run(self, audio_path: str) -> List[Segment]:
        model = self._load_model()
        segments_iter, _info = model.transcribe(
            audio_path,
            language=self.language,
            **self.extra_kwargs,
        )

        segments = []
        for seg in segments_iter:
            segments.append(Segment(start=float(seg.start), end=float(seg.end), text=seg.text))
        return segments
