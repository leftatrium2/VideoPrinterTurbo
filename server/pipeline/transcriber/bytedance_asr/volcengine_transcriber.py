import base64
import logging
import time
import uuid
from typing import Optional, List

import requests

from pipeline.transcriber.base import BaseTranscriber
from pipeline.transcriber.segment import Segment
from pipeline.transcriber.utils.asr_utils import build_proxies, get_duration_seconds, split_audio_by_duration, \
    segments_to_srt, cleanup_dir

logger = logging.getLogger(__name__)

_SUBMIT_URL = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/submit"
_QUERY_URL = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/query"
_RESOURCE_ID = "volc.bigasr.auc"

# 官方文档未给出明确单文件时长/大小上限，这里给一个保守的默认分片阈值，可按需调整
_DEFAULT_MAX_CHUNK_SECONDS = 60 * 60


#     火山引擎「大模型录音文件识别」转写实现。
#
#     音频以 base64 直接放入请求体（audio.data），无需先上传到公网可访问的存储。
#     流程：submit（提交任务）-> query（轮询直至完成，通过响应头 X-Api-Status-Code 判断状态）。
#     参考文档: https://www.volcengine.com/docs/6561/1631584
class VolcengineASR(BaseTranscriber):
    def __init__(
            self,
            app_id: str,
            access_token: str,
            audio_format: str = "wav",
            enable_punc: bool = True,
            max_chunk_seconds: int = _DEFAULT_MAX_CHUNK_SECONDS,
            poll_interval_seconds: float = 3.0,
            poll_timeout_seconds: float = 1800.0,
    ):
        self.app_id = app_id
        self.access_token = access_token
        self.audio_format = audio_format
        self.enable_punc = enable_punc
        self.max_chunk_seconds = max_chunk_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.poll_timeout_seconds = poll_timeout_seconds
        self.proxies = None

    def config(self, proxy: Optional[str] = None):
        if proxy:
            self.proxies = build_proxies(proxy)

    def transcribe(self, audio_path: str) -> Optional[str]:
        tmp_dir = None
        try:
            duration = get_duration_seconds(audio_path)
            if duration <= self.max_chunk_seconds:
                segments = self._transcribe_single_file(audio_path)
            else:
                import tempfile
                tmp_dir = tempfile.mkdtemp(prefix="volc_asr_")
                chunks = split_audio_by_duration(
                    audio_path, chunk_seconds=self.max_chunk_seconds, out_dir=tmp_dir,
                    sample_rate=16000, channels=1, audio_format="wav",
                )
                segments = []
                offset = 0.0
                remaining = duration
                for c in chunks:
                    this_duration = min(self.max_chunk_seconds, remaining)
                    segments.extend(s.shifted(offset) for s in self._transcribe_single_file(c, force_format="wav"))
                    offset += this_duration
                    remaining -= this_duration

            if not segments:
                logger.warning(f"[VolcengineASRTranscriber] 未识别到任何内容: {audio_path}")
                return None
            return segments_to_srt(segments)
        except Exception as e:
            logger.error(f"[VolcengineASRTranscriber] 转写失败: {audio_path}, 错误: {e}", exc_info=True)
            return None
        finally:
            if tmp_dir:
                cleanup_dir(tmp_dir)

    def _transcribe_single_file(self, audio_path: str, force_format: Optional[str] = None) -> List[Segment]:
        task_id = self._submit(audio_path, force_format=force_format)
        return self._poll_and_get_result(task_id)

    def _headers(self, task_id: str) -> dict:
        return {
            "X-Api-App-Key": self.app_id,
            "X-Api-Access-Key": self.access_token,
            "X-Api-Resource-Id": _RESOURCE_ID,
            "X-Api-Request-Id": task_id,
            "X-Api-Sequence": "-1",
        }

    def _submit(self, audio_path: str, force_format: Optional[str] = None) -> str:
        task_id = str(uuid.uuid4())
        with open(audio_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode("utf-8")

        payload = {
            "user": {"uid": self.app_id},
            "audio": {
                "format": force_format or self.audio_format,
                "data": audio_b64,
            },
            "request": {
                "model_name": "bigmodel",
                "enable_itn": True,
                "enable_punc": self.enable_punc,
                "show_utterances": True,
            },
        }
        resp = requests.post(_SUBMIT_URL, json=payload, headers=self._headers(task_id), timeout=120,
                             proxies=self.proxies)
        status_code = resp.headers.get("X-Api-Status-Code")
        if status_code not in (None, "20000000"):
            raise RuntimeError(f"火山引擎提交任务失败 [{status_code}]: {resp.headers.get('X-Api-Message')}")
        return task_id

    def _poll_and_get_result(self, task_id: str) -> List[Segment]:
        deadline = time.time() + self.poll_timeout_seconds
        while time.time() < deadline:
            resp = requests.post(_QUERY_URL, json={}, headers=self._headers(task_id), timeout=60, proxies=self.proxies)
            status_code = resp.headers.get("X-Api-Status-Code")

            if status_code == "20000000":  # 任务完成
                data = resp.json()
                return self._parse_utterances(data)
            if status_code in ("20000001", "20000002"):  # 排队中/处理中
                time.sleep(self.poll_interval_seconds)
                continue
            if status_code is None:
                time.sleep(self.poll_interval_seconds)
                continue
            raise RuntimeError(f"火山引擎查询任务失败 [{status_code}]: {resp.headers.get('X-Api-Message')}")

        raise TimeoutError(f"火山引擎识别任务轮询超时: task_id={task_id}")

    @staticmethod
    def _parse_utterances(data: dict) -> List[Segment]:
        result = data.get("result", {})
        utterances = result.get("utterances", [])
        segments = []
        for u in utterances:
            start_ms = u.get("start_time", 0)
            end_ms = u.get("end_time", 0)
            text = u.get("text", "")
            segments.append(Segment(start=start_ms / 1000.0, end=end_ms / 1000.0, text=text))
        return segments
