import base64
import hashlib
import hmac
import json
import logging
import time
from typing import List, Optional

import requests

from pipeline.transcriber.base import BaseTranscriber
from pipeline.transcriber.segment import Segment
from pipeline.transcriber.utils.asr_utils import get_duration_seconds, segments_to_srt, cleanup_dir, build_proxies, \
    convert_audio, split_audio_by_duration

logger = logging.getLogger(__name__)

_HOST = "asr.tencentcloudapi.com"
_SERVICE = "asr"
_VERSION = "2019-06-14"
_ALGORITHM = "TC3-HMAC-SHA256"

# 单文件 Data(base64) 上传方式官方建议控制在较小体积内，超过该阈值自动切片处理。
# 可通过构造函数的 max_chunk_seconds 自行调整分片粒度。
_DEFAULT_MAX_CHUNK_SECONDS = 20 * 60  # 20 分钟一片，规避单次上传体积/时长过大问题


# 腾讯云「录音文件识别」转写实现。
#
#     使用 CreateRecTask（SourceType=1，本地音频 base64 直传）+ DescribeTaskStatus 轮询。
#     参考文档：
#       - https://cloud.tencent.com/document/product/1093/37823 (CreateRecTask)
#       - https://cloud.tencent.com/document/product/1093/37822 (DescribeTaskStatus)
class TencentCloudTranscriber(BaseTranscriber):
    def __init__(
            self,
            secret_id: str,
            secret_key: str,
            app_id: str = "",
            region: str = "ap-shanghai",
            engine_model_type: str = "16k_zh",
            max_chunk_seconds: int = _DEFAULT_MAX_CHUNK_SECONDS,
            poll_interval_seconds: float = 3.0,
            poll_timeout_seconds: float = 600.0,
    ):
        self.proxies = None
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.app_id = app_id
        self.region = region
        self.engine_model_type = engine_model_type
        self.max_chunk_seconds = max_chunk_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.poll_timeout_seconds = poll_timeout_seconds

    def config(self, proxy: Optional[str] = None):
        if proxy:
            self.proxies = build_proxies(proxy)

    def transcribe(self, audio_path: str) -> Optional[str]:
        tmp_dir = None
        try:
            duration = get_duration_seconds(audio_path)
            chunk_plan = self._plan_chunks(audio_path, duration)
            chunk_paths, tmp_dir = chunk_plan

            all_segments: List[Segment] = []
            offset = 0.0
            for chunk_path, chunk_duration in chunk_paths:
                segs = self._transcribe_single_file(chunk_path)
                all_segments.extend(s.shifted(offset) for s in segs)
                offset += chunk_duration

            if not all_segments:
                logger.warning(f"[TencentASRTranscriber] 未识别到任何内容: {audio_path}")
                return None
            return segments_to_srt(all_segments)
        except Exception as e:
            logger.error(f"[TencentASRTranscriber] 转写失败: {audio_path}, 错误: {e}", exc_info=True)
            return None
        finally:
            if tmp_dir:
                cleanup_dir(tmp_dir)

    # ---------------------------- 分片规划 ----------------------------

    def _plan_chunks(self, audio_path: str, duration: float):
        """
        返回 ([(chunk_path, chunk_duration_seconds), ...], tmp_dir_or_None)
        统一先转成 16k 单声道 wav（腾讯云录音识别推荐格式），
        超过 max_chunk_seconds 时自动分片。
        """
        import os
        import tempfile

        if duration <= self.max_chunk_seconds:
            tmp_dir = tempfile.mkdtemp(prefix="tencent_asr_")
            converted = os.path.join(tmp_dir, "audio.wav")
            convert_audio(audio_path, converted, sample_rate=16000, channels=1, audio_format="wav")
            return [(converted, duration)], tmp_dir

        tmp_dir = tempfile.mkdtemp(prefix="tencent_asr_")
        chunks = split_audio_by_duration(
            audio_path,
            chunk_seconds=self.max_chunk_seconds,
            out_dir=tmp_dir,
            sample_rate=16000,
            channels=1,
            audio_format="wav",
        )
        result = []
        remaining = duration
        for c in chunks:
            this_duration = min(self.max_chunk_seconds, remaining)
            result.append((c, this_duration))
            remaining -= this_duration
        return result, tmp_dir

    # ---------------------------- 单片识别 ----------------------------

    def _transcribe_single_file(self, audio_path: str) -> List[Segment]:
        with open(audio_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode("utf-8")

        create_payload = {
            "EngineModelType": self.engine_model_type,
            "ChannelNum": 1,
            "ResTextFormat": 0,
            "SourceType": 1,
            "Data": audio_b64,
        }
        create_resp = self._call_api("CreateRecTask", create_payload)
        task_id = create_resp["Response"]["Data"]["TaskId"]

        return self._poll_task(task_id)

    def _poll_task(self, task_id: int) -> List[Segment]:
        deadline = time.time() + self.poll_timeout_seconds
        while time.time() < deadline:
            resp = self._call_api("DescribeTaskStatus", {"TaskId": task_id})
            data = resp["Response"]["Data"]
            status_str = data.get("StatusStr")

            if status_str == "success":
                return self._parse_result_detail(data.get("ResultDetail", []))
            if status_str == "failed":
                raise RuntimeError(f"腾讯云识别任务失败: {data.get('ErrorMsg')}")

            time.sleep(self.poll_interval_seconds)

        raise TimeoutError(f"腾讯云识别任务轮询超时: TaskId={task_id}")

    @staticmethod
    def _parse_result_detail(result_detail: list) -> List[Segment]:
        segments = []
        for item in result_detail:
            start_ms = item.get("StartMs", 0)
            end_ms = item.get("EndMs", 0)
            text = item.get("FinalSentence", "")
            segments.append(Segment(start=start_ms / 1000.0, end=end_ms / 1000.0, text=text))
        return segments

    # ---------------------------- TC3-HMAC-SHA256 签名 & 请求 ----------------------------

    def _call_api(self, action: str, payload: dict) -> dict:
        timestamp = int(time.time())
        payload_str = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)

        headers = self._build_signed_headers(action, timestamp, payload_str)
        resp = requests.post(
            f"https://{_HOST}",
            headers=headers,
            data=payload_str.encode("utf-8"),
            timeout=30,
            proxies=self.proxies,
        )
        resp.raise_for_status()
        data = resp.json()
        if "Error" in data.get("Response", {}):
            err = data["Response"]["Error"]
            raise RuntimeError(f"腾讯云 API 错误 [{err.get('Code')}]: {err.get('Message')}")
        return data

    def _build_signed_headers(self, action: str, timestamp: int, payload_str: str) -> dict:
        date = time.strftime("%Y-%m-%d", time.gmtime(timestamp))

        # ---- Step 1: 拼接规范请求串 ----
        http_method = "POST"
        canonical_uri = "/"
        canonical_querystring = ""
        content_type = "application/json; charset=utf-8"
        canonical_headers = (
            f"content-type:{content_type}\n"
            f"host:{_HOST}\n"
            f"x-tc-action:{action.lower()}\n"
        )
        signed_headers = "content-type;host;x-tc-action"
        hashed_payload = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        canonical_request = "\n".join([
            http_method, canonical_uri, canonical_querystring,
            canonical_headers, signed_headers, hashed_payload,
        ])

        # ---- Step 2: 拼接待签名字符串 ----
        credential_scope = f"{date}/{_SERVICE}/tc3_request"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign = "\n".join([
            _ALGORITHM, str(timestamp), credential_scope, hashed_canonical_request,
        ])

        # ---- Step 3: 计算签名 ----
        def _hmac_sha256(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        secret_date = _hmac_sha256(("TC3" + self.secret_key).encode("utf-8"), date)
        secret_service = _hmac_sha256(secret_date, _SERVICE)
        secret_signing = _hmac_sha256(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        # ---- Step 4: 拼接 Authorization ----
        authorization = (
            f"{_ALGORITHM} "
            f"Credential={self.secret_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

        headers = {
            "Authorization": authorization,
            "Content-Type": content_type,
            "Host": _HOST,
            "X-TC-Action": action,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Version": _VERSION,
            "X-TC-Region": self.region,
        }
        if self.app_id:
            headers["X-TC-AppId"] = str(self.app_id)
        return headers
