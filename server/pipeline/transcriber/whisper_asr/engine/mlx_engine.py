import logging
from typing import List

from pipeline.transcriber.segment import Segment
from pipeline.transcriber.whisper_asr.engine.base_engine import BaseWhisperEngine

logger = logging.getLogger(__name__)

# mlx_whisper 官方仓库中常见的模型命名规则（HuggingFace repo），
# 允许用户直接传完整 repo id，也允许传简写（如 "large-v3"）自动补全。
_MLX_REPO_PREFIX = "mlx-community/whisper-"


class MLXWhisperEngine(BaseWhisperEngine):
    """
    基于 mlx-whisper 的本地推理引擎。
    仅支持 Apple Silicon (M系列芯片) + macOS，依赖 `pip install mlx-whisper`。
    """

    def _resolve_repo(self) -> str:
        if "/" in self.model_size:
            # 用户直接传入了完整的 HuggingFace repo id
            return self.model_size
        return f"{_MLX_REPO_PREFIX}{self.model_size}"

    def run(self, audio_path: str) -> List[Segment]:
        try:
            import mlx_whisper
        except ImportError as e:
            raise ImportError(
                "未安装 mlx-whisper，请先执行 `pip install mlx-whisper`（仅支持 Apple Silicon）。"
            ) from e

        repo = self._resolve_repo()
        logger.info(f"[MLXWhisperEngine] 使用模型: {repo}")

        result = mlx_whisper.transcribe(
            audio_path,
            path_or_hf_repo=repo,
            language=self.language,
            **self.extra_kwargs,
        )

        segments = []
        for seg in result.get("segments", []):
            text = seg.get("text", "")
            segments.append(
                Segment(start=float(seg["start"]), end=float(seg["end"]), text=text)
            )
        return segments
