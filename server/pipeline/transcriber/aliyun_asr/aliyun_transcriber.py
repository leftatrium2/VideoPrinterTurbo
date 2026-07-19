import logging
import time
from typing import Optional, List

import requests

from pipeline.transcriber.base import BaseTranscriber
from pipeline.transcriber.segment import Segment
from pipeline.transcriber.utils.asr_utils import build_proxies, segments_to_srt

logger = logging.getLogger(__name__)

_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"
_SUBMIT_URL = f"{_BASE_URL}/services/audio/asr/transcription"
_UPLOAD_POLICY_URL = f"{_BASE_URL}/uploads"


#     阿里云百炼(DashScope) 录音文件识别转写实现（Paraformer 系列模型）。
#
#     DashScope 的录音文件识别接口要求音频以 file_urls 形式提供（必须是可公网访问的 URL），
#     因此本类会先调用其「文件上传凭证」接口，把本地文件上传到 DashScope 提供的临时 OSS，
#     得到 oss:// 形式的 URL 后再提交任务——不需要用户自备 OSS Bucket。
#
#     参考文档:
#       - https://help.aliyun.com/zh/model-studio/paraformer-recorded-speech-recognition-restful-api
#       - https://help.aliyun.com/zh/model-studio/upload-file (文件上传凭证)
class AliyunASR(BaseTranscriber):
    def __init__(
            self,
            api_key: str,
            model: str = "paraformer-v2",
            poll_interval_seconds: float = 5.0,
            poll_timeout_seconds: float = 1800.0,
    ):
        self.proxies = None
        self.api_key = api_key
        self.model = model
        self.poll_interval_seconds = poll_interval_seconds
        self.poll_timeout_seconds = poll_timeout_seconds

    def config(self, proxy: Optional[str] = None):
        if proxy:
            self.proxies = build_proxies(proxy)

    def transcribe(self, audio_path: str) -> Optional[str]:
        try:
            file_url = self._upload_local_file(audio_path)
            task_id = self._submit_task(file_url)
            segments = self._poll_and_parse(task_id)
            if not segments:
                logger.warning(f"[AliyunASRTranscriber] 未识别到任何内容: {audio_path}")
                return None
            return segments_to_srt(segments)
        except Exception as e:
            logger.error(f"[AliyunASRTranscriber] 转写失败: {audio_path}, 错误: {e}", exc_info=True)
            return None

    # ---------------------------- 文件上传凭证：本地文件 -> 临时可访问 URL ----------------------------

    def _upload_local_file(self, audio_path: str) -> str:
        file_name = audio_path.split("/")[-1]

        # 1) 获取上传凭证
        headers = {"Authorization": f"Bearer {self.api_key}"}
        policy_resp = requests.get(
            _UPLOAD_POLICY_URL,
            headers=headers,
            params={"action": "getPolicy", "model": self.model},
            timeout=30,
            proxies=self.proxies,
        )
        policy_resp.raise_for_status()
        policy = policy_resp.json()["data"]

        # 2) 按凭证以 multipart/form-data 方式 POST 到 OSS
        upload_fields = {
            "OSSAccessKeyId": policy["oss_access_key_id"],
            "Signature": policy["signature"],
            "policy": policy["policy"],
            "x-oss-object-acl": policy["x_oss_object_acl"],
            "x-oss-forbid-overwrite": policy["x_oss_forbid_overwrite"],
            "key": f"{policy['upload_dir']}/{file_name}",
            "success_action_status": "200",
        }
        with open(audio_path, "rb") as f:
            files = {"file": (file_name, f)}
            upload_resp = requests.post(policy["upload_host"], data=upload_fields, files=files, timeout=300,
                                        proxies=self.proxies)
        if upload_resp.status_code != 200:
            raise RuntimeError(f"阿里云 DashScope 文件上传失败 [{upload_resp.status_code}]: {upload_resp.text}")

        return f"oss://{upload_fields['key']}"

    # ---------------------------- 提交任务 & 轮询 ----------------------------

    def _submit_task(self, file_url: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }
        payload = {
            "model": self.model,
            "input": {"file_urls": [file_url]},
            "parameters": {"channel_id": [0]},
        }
        resp = requests.post(_SUBMIT_URL, headers=headers, json=payload, timeout=30, proxies=self.proxies)
        resp.raise_for_status()
        data = resp.json()
        if "output" not in data or "task_id" not in data["output"]:
            raise RuntimeError(f"阿里云 DashScope 提交任务失败: {data}")
        return data["output"]["task_id"]

    def _poll_and_parse(self, task_id: str) -> List[Segment]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        task_url = f"{_BASE_URL}/tasks/{task_id}"
        deadline = time.time() + self.poll_timeout_seconds

        while time.time() < deadline:
            resp = requests.get(task_url, headers=headers, timeout=30, proxies=self.proxies)
            resp.raise_for_status()
            data = resp.json()
            status = data.get("output", {}).get("task_status")

            if status == "SUCCEEDED":
                return self._parse_result(data["output"])
            if status == "FAILED":
                raise RuntimeError(f"阿里云 DashScope 识别任务失败: {data['output']}")

            time.sleep(self.poll_interval_seconds)

        raise TimeoutError(f"阿里云 DashScope 识别任务轮询超时: task_id={task_id}")

    def _parse_result(self, output: dict) -> List[Segment]:
        segments = []
        results = output.get("results", [])
        for r in results:
            transcription_url = r.get("transcription_url")
            if not transcription_url:
                continue
            resp = requests.get(transcription_url, timeout=60, proxies=self.proxies)
            resp.raise_for_status()
            transcript_data = resp.json()
            for t in transcript_data.get("transcripts", []):
                for sentence in t.get("sentences", []):
                    begin_ms = sentence.get("begin_time", 0)
                    end_ms = sentence.get("end_time", 0)
                    text = sentence.get("text", "")
                    segments.append(Segment(start=begin_ms / 1000.0, end=end_ms / 1000.0, text=text))
        return segments
