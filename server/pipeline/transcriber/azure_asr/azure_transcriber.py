import json
import logging
from typing import Optional, List

import requests

from pipeline.transcriber.base import BaseTranscriber
from pipeline.transcriber.segment import Segment
from pipeline.transcriber.utils.asr_utils import build_proxies, get_duration_seconds, split_audio_by_duration, \
    segments_to_srt, cleanup_dir

logger = logging.getLogger(__name__)

_API_VERSION = "2024-11-15"
# 官方硬限制 5 小时/500MB，这里保守地按时长切分，避免单次同步请求过大/超时
_DEFAULT_MAX_CHUNK_SECONDS = 90 * 60


class AzureASR(BaseTranscriber):
    def __init__(
            self,
            subscription_key: str,
            region: str,
            locales: Optional[List[str]] = None,
            enable_diarization: bool = False,
            max_chunk_seconds: int = _DEFAULT_MAX_CHUNK_SECONDS,
            proxy: Optional[str] = None,
    ):
        self.proxies = None
        self.subscription_key = subscription_key
        self.region = region
        # locale 未知时可传多个候选，服务会自动挑选最匹配的（也可传 None 走语种自动识别的默认行为）
        self.locales = locales or ["zh-CN", "en-US"]
        self.enable_diarization = enable_diarization
        self.max_chunk_seconds = max_chunk_seconds
        self.proxies = build_proxies(proxy)

    def config(self, proxy: Optional[str] = None):
        if proxy:
            self.proxies = build_proxies(proxy)

    def transcribe(self, audio_path: str) -> Optional[str]:
        tmp_dir = None
        try:
            duration = get_duration_seconds(audio_path)
            if duration <= self.max_chunk_seconds:
                segments = self._call_fast_transcription(audio_path)
            else:
                import tempfile
                tmp_dir = tempfile.mkdtemp(prefix="azure_asr_")
                chunks = split_audio_by_duration(
                    audio_path, chunk_seconds=self.max_chunk_seconds, out_dir=tmp_dir,
                    sample_rate=16000, channels=1, audio_format="wav",
                )
                segments = []
                offset = 0.0
                remaining = duration
                for c in chunks:
                    this_duration = min(self.max_chunk_seconds, remaining)
                    segments.extend(s.shifted(offset) for s in self._call_fast_transcription(c))
                    offset += this_duration
                    remaining -= this_duration

            if not segments:
                logger.warning(f"[AzureASRTranscriber] 未识别到任何内容: {audio_path}")
                return None
            return segments_to_srt(segments)
        except Exception as e:
            logger.error(f"[AzureASRTranscriber] 转写失败: {audio_path}, 错误: {e}", exc_info=True)
            return None
        finally:
            if tmp_dir:
                cleanup_dir(tmp_dir)

    def _call_fast_transcription(self, audio_path: str) -> List[Segment]:
        url = (
            f"https://{self.region}.api.cognitive.microsoft.com"
            f"/speechtotext/transcriptions:transcribe?api-version={_API_VERSION}"
        )
        definition = {"locales": self.locales}
        if self.enable_diarization:
            definition["diarization"] = {"enabled": True, "maxSpeakers": 8}

        with open(audio_path, "rb") as f:
            files = {
                "audio": (audio_path.split("/")[-1], f, "application/octet-stream"),
                "definition": (None, json.dumps(definition), "application/json"),
            }
            headers = {"Ocp-Apim-Subscription-Key": self.subscription_key}
            resp = requests.post(url, headers=headers, files=files, timeout=600, proxies=self.proxies)

        if resp.status_code != 200:
            raise RuntimeError(f"Azure fast transcription 请求失败 [{resp.status_code}]: {resp.text}")

        data = resp.json()
        segments = []
        for phrase in data.get("phrases", []):
            start = phrase.get("offsetMilliseconds", 0) / 1000.0
            duration = phrase.get("durationMilliseconds", 0) / 1000.0
            text = phrase.get("text", "")
            segments.append(Segment(start=start, end=start + duration, text=text))
        return segments
