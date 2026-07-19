import logging
from typing import Optional, List

from pipeline.transcriber.base import BaseTranscriber
from pipeline.transcriber.segment import Segment
from pipeline.transcriber.utils.asr_utils import get_file_size, get_duration_seconds, \
    split_audio_by_duration, segments_to_srt, cleanup_dir

logger = logging.getLogger(__name__)

# OpenAI 官方单文件大小限制 25MB，超过则按时长切分后转码压缩体积
_MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024
_DEFAULT_MAX_CHUNK_SECONDS = 20 * 60  # 经验值：20 分钟的 16k 单声道音频通常在限制内


class OpenAIASR(BaseTranscriber):
    def __init__(
            self,
            api_key: str,
            model: str = "whisper-1",
            language: Optional[str] = None,
            base_url: Optional[str] = None,
            max_chunk_seconds: int = _DEFAULT_MAX_CHUNK_SECONDS,
    ):
        self.api_key = api_key
        self.model = model
        self.language = language
        self.base_url = base_url
        self.max_chunk_seconds = max_chunk_seconds
        self.proxy = None
        self._client = None

    def config(self, proxy: Optional[str] = None):
        if proxy:
            self.proxy = proxy

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as e:
                raise ImportError("未安装 openai，请先执行 `pip install openai`。") from e
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            if self.proxy:
                try:
                    import httpx
                except ImportError as e:
                    raise ImportError(
                        "使用 proxy 参数需要 httpx（openai 包的依赖之一，通常已随其一起安装），"
                        "如缺失请执行 `pip install httpx`。"
                    ) from e
                kwargs["http_client"] = httpx.Client(proxy=self.proxy)
            self._client = OpenAI(**kwargs)
        return self._client

    def transcribe(self, audio_path: str) -> Optional[str]:
        tmp_dir = None
        try:
            size = get_file_size(audio_path)
            if size <= _MAX_FILE_SIZE_BYTES:
                segments = self._transcribe_single_file(audio_path)
            else:
                import tempfile

                tmp_dir = tempfile.mkdtemp(prefix="openai_asr_")
                duration = get_duration_seconds(audio_path)
                chunks = split_audio_by_duration(
                    audio_path, chunk_seconds=self.max_chunk_seconds, out_dir=tmp_dir,
                    sample_rate=16000, channels=1, audio_format="mp3",
                )
                segments = []
                offset = 0.0
                remaining = duration
                for c in chunks:
                    this_duration = min(self.max_chunk_seconds, remaining)
                    segments.extend(s.shifted(offset) for s in self._transcribe_single_file(c))
                    offset += this_duration
                    remaining -= this_duration

            if not segments:
                logger.warning(f"[OpenAIASRTranscriber] 未识别到任何内容: {audio_path}")
                return None
            return segments_to_srt(segments)
        except Exception as e:
            logger.error(f"[OpenAIASRTranscriber] 转写失败: {audio_path}, 错误: {e}", exc_info=True)
            return None
        finally:
            if tmp_dir:
                cleanup_dir(tmp_dir)

    def _transcribe_single_file(self, audio_path: str) -> List[Segment]:
        client = self._get_client()
        with open(audio_path, "rb") as f:
            resp = client.audio.transcriptions.create(
                model=self.model,
                file=f,
                language=self.language,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )

        segments = []
        raw_segments = getattr(resp, "segments", None) or []
        for seg in raw_segments:
            # SDK 返回对象既可能是 dict 也可能是带属性的对象，两种都兼容
            start = seg["start"] if isinstance(seg, dict) else seg.start
            end = seg["end"] if isinstance(seg, dict) else seg.end
            text = seg["text"] if isinstance(seg, dict) else seg.text
            segments.append(Segment(start=float(start), end=float(end), text=text))
        return segments
