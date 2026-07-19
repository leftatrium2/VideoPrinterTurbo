import logging
from typing import Optional

from pipeline.transcriber.utils.asr_utils import segments_to_srt
from pipeline.transcriber.base import BaseTranscriber
from pipeline.transcriber.whisper_asr.engine.faster_engine import FasterWhisperEngine
from pipeline.transcriber.whisper_asr.engine.mlx_engine import MLXWhisperEngine
from pipeline.transcriber.whisper_asr.engine.openai_engine import OpenAIWhisperEngine
from utils.const import TASK_CONFIG_ASR_OPENAI_WHISPER, TASK_CONFIG_ASR_MLX_WHISPER, TASK_CONFIG_ASR_FASTER_WHISPER

logger = logging.getLogger(__name__)

_ENGINE_MAP = {
    TASK_CONFIG_ASR_MLX_WHISPER: MLXWhisperEngine,
    TASK_CONFIG_ASR_FASTER_WHISPER: FasterWhisperEngine,
    TASK_CONFIG_ASR_OPENAI_WHISPER: OpenAIWhisperEngine,
}


#     Whisper 统一转写实现类。
#
#     通过 set_local_whisper_type(type_id) 指定底层使用哪种 Whisper 实现：
#         TASK_CONFIG_ASR_MLX_WHISPER = 1     -> mlx-whisper（Apple Silicon）
#         TASK_CONFIG_ASR_FASTER_WHISPER = 2  -> faster-whisper
#         TASK_CONFIG_ASR_OPENAI_WHISPER = 3  -> openai-whisper（官方实现）
class WhisperTranscriber(BaseTranscriber):
    def __init__(
            self,
            local_whisper_type: int = TASK_CONFIG_ASR_OPENAI_WHISPER,
            model_size: str = "large-v3",
            language: Optional[str] = None,
            **engine_kwargs,
    ):
        self.__proxy = None
        self._local_whisper_type = local_whisper_type
        self._model_size = model_size
        self._language = language
        self._engine_kwargs = engine_kwargs
        self._engine = None  # 惰性创建，type 变化时会重建

    def set_local_whisper_type(self, local_whisper_type: int):
        """切换底层 Whisper 实现类型，下次 transcribe() 时会重新创建对应引擎"""
        if local_whisper_type not in _ENGINE_MAP:
            raise ValueError(f"未知的 local_whisper_type: {local_whisper_type}")
        if local_whisper_type != self._local_whisper_type:
            self._engine = None
        self._local_whisper_type = local_whisper_type

    def _get_engine(self):
        if self._engine is None:
            engine_cls = _ENGINE_MAP.get(self._local_whisper_type)
            if engine_cls is None:
                raise ValueError(f"未知的 local_whisper_type: {self._local_whisper_type}")
            self._engine = engine_cls(
                model_size=self._model_size,
                language=self._language,
                **self._engine_kwargs,
            )
        return self._engine

    def config(self, proxy: str = None):
        self.__proxy = proxy

    def transcribe(self, audio_path: str) -> Optional[str]:
        try:
            engine = self._get_engine()
            segments = engine.run(audio_path)
            if not segments:
                logger.warning(f"[WhisperTranscriber] 未识别到任何内容: {audio_path}")
                return None
            return segments_to_srt(segments)
        except Exception as e:
            logger.error(f"[WhisperTranscriber] 转写失败: {audio_path}, 错误: {e}", exc_info=True)
            return None
