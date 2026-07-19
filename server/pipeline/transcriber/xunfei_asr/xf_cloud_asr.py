import base64
import hashlib
import hmac
import json
import logging
import time
from typing import Optional, List, Tuple

import requests

from pipeline.transcriber.base import BaseTranscriber
from pipeline.transcriber.segment import Segment
from pipeline.transcriber.utils.asr_utils import get_duration_seconds, get_file_size, segments_to_srt, cleanup_dir, \
    split_audio_by_duration, build_proxies

logger = logging.getLogger(__name__)

_API_BASE = "https://raasr.xfyun.cn/api"
_SLICE_SIZE = 10 * 1024 * 1024  # 10MB，官方建议分片大小

# 官方限制：单文件不超过 500M，音频时长不超过 5 小时。
# 此处默认更保守地切分（时长维度），避免逼近限制导致失败；可通过构造函数调整。
_DEFAULT_MAX_CHUNK_SECONDS = 2 * 60 * 60  # 2 小时一片
_DEFAULT_MAX_FILE_SIZE = 480 * 1024 * 1024  # 480MB，预留安全余量

# 任务状态：9 = 转写结果上传完成
_STATUS_DONE = 9


class _SliceIdGenerator:
    """按讯飞demo规则生成分片序号：aaaaaaaaaa, aaaaaaaaab, ..."""

    def __init__(self):
        self._ch = "aaaaaaaaa`"

    def next_id(self) -> str:
        ch = self._ch
        j = len(ch) - 1
        while j >= 0:
            cj = ch[j]
            if cj != "z":
                ch = ch[:j] + chr(ord(cj) + 1) + ch[j + 1:]
                break
            else:
                ch = ch[:j] + "a" + ch[j + 1:]
                j -= 1
        self._ch = ch
        return self._ch


#     科大讯飞「语音转写（长音频）」转写实现。
#
#     流程：预处理(prepare) -> 分片上传(upload) -> 合并(merge) -> 轮询进度(getProgress) -> 取结果(getResult)
#     参考文档: https://www.xfyun.cn/doc/asr/lfasr/API.html
class XFCloudASR(BaseTranscriber):
    def __init__(
            self,
            app_id: str,
            api_key: str,
            api_secret: str,
            language: str = "cn",
            max_chunk_seconds: int = _DEFAULT_MAX_CHUNK_SECONDS,
            max_file_size_bytes: int = _DEFAULT_MAX_FILE_SIZE,
            poll_interval_seconds: float = 15.0,
            poll_timeout_seconds: float = 3600.0,
    ):
        # 注意：讯飞长音频转写鉴权使用的是"接口密钥(secret_key)"，
        # 这里沿用 api_secret 命名以便与其他实时接口的 api_key/api_secret 概念区分统一。
        self.proxies = None
        self.app_id = app_id
        self.api_key = api_key
        self.secret_key = api_secret
        self.language = language
        self.max_chunk_seconds = max_chunk_seconds
        self.max_file_size_bytes = max_file_size_bytes
        self.poll_interval_seconds = poll_interval_seconds
        self.poll_timeout_seconds = poll_timeout_seconds

    def config(self, proxy: Optional[str] = None):
        if proxy:
            self.proxies = build_proxies(proxy)

    def transcribe(self, audio_path: str) -> Optional[str]:
        tmp_dir = None
        try:
            duration = get_duration_seconds(audio_path)
            size = get_file_size(audio_path)

            chunk_paths, tmp_dir = self._plan_chunks(audio_path, duration, size)

            all_segments: List[Segment] = []
            offset = 0.0
            for chunk_path, chunk_duration in chunk_paths:
                segs = self._transcribe_single_file(chunk_path)
                all_segments.extend(s.shifted(offset) for s in segs)
                offset += chunk_duration

            if not all_segments:
                logger.warning(f"[XunfeiASRTranscriber] 未识别到任何内容: {audio_path}")
                return None
            return segments_to_srt(all_segments)
        except Exception as e:
            logger.error(f"[XunfeiASRTranscriber] 转写失败: {audio_path}, 错误: {e}", exc_info=True)
            return None
        finally:
            if tmp_dir:
                cleanup_dir(tmp_dir)

    # ---------------------------- 分片规划 ----------------------------
    def _plan_chunks(self, audio_path: str, duration: float, size: int) -> Tuple[
        List[Tuple[str, float]], Optional[str]]:
        """
        讯飞原生支持 wav/flac/opus/m4a/mp3，8k/16k，单文件 500M/5小时以内，
        因此未超限时无需转码，直接整段提交；超限才切分（并统一转码为 wav 16k 单声道，规避原始编码切分产生的解码问题）。
        """
        if duration <= self.max_chunk_seconds and size <= self.max_file_size_bytes:
            return [(audio_path, duration)], None

        import tempfile
        tmp_dir = tempfile.mkdtemp(prefix="xunfei_asr_")
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
            file_bytes = f.read()
        file_len = len(file_bytes)
        file_name = audio_path.split("/")[-1]

        task_id = self._prepare(file_len=file_len, file_name=file_name, slice_num=self._calc_slice_num(file_len))
        self._upload_slices(task_id, file_bytes)
        self._merge(task_id)
        self._wait_until_done(task_id)
        return self._get_result(task_id)

    @staticmethod
    def _calc_slice_num(file_len: int) -> int:
        if file_len <= _SLICE_SIZE:
            return 1
        return (file_len + _SLICE_SIZE - 1) // _SLICE_SIZE

    # ---------------------------- signa 签名 ----------------------------
    def _build_signa(self, ts: str) -> str:
        """signa = base64(HmacSHA1(MD5(appid + ts), secret_key))"""
        base_string = f"{self.app_id}{ts}"
        md5_hex = hashlib.md5(base_string.encode("utf-8")).hexdigest()
        signa_bytes = hmac.new(
            self.secret_key.encode("utf-8"),
            md5_hex.encode("utf-8"),
            hashlib.sha1,
        ).digest()
        return base64.b64encode(signa_bytes).decode("utf-8")

    def _common_params(self) -> dict:
        ts = str(int(time.time()))
        return {
            "app_id": self.app_id,
            "signa": self._build_signa(ts),
            "ts": ts,
        }

    # ---------------------------- 各接口调用 ----------------------------

    def _prepare(self, file_len: int, file_name: str, slice_num: int) -> str:
        params = self._common_params()
        params.update({
            "file_len": str(file_len),
            "file_name": file_name,
            "slice_num": str(slice_num),
            "language": self.language,
        })
        resp = requests.post(f"{_API_BASE}/prepare", data=params, timeout=30).json()
        self._check_ok(resp, "prepare")
        return resp["data"]

    def _upload_slices(self, task_id: str, file_bytes: bytes) -> None:
        slice_gen = _SliceIdGenerator()
        for start in range(0, len(file_bytes), _SLICE_SIZE):
            chunk = file_bytes[start:start + _SLICE_SIZE]
            slice_id = slice_gen.next_id()
            params = self._common_params()
            params.update({"task_id": task_id, "slice_id": slice_id})
            files = {"content": (slice_id, chunk)}
            resp = requests.post(f"{_API_BASE}/upload", data=params, files=files, timeout=60).json()
            self._check_ok(resp, "upload")

    def _merge(self, task_id: str) -> None:
        params = self._common_params()
        params.update({"task_id": task_id})
        resp = requests.post(f"{_API_BASE}/merge", data=params, timeout=30).json()
        self._check_ok(resp, "merge")

    def _wait_until_done(self, task_id: str) -> None:
        deadline = time.time() + self.poll_timeout_seconds
        while time.time() < deadline:
            params = self._common_params()
            params.update({"task_id": task_id})
            resp = requests.post(f"{_API_BASE}/getProgress", data=params, timeout=30).json()
            self._check_ok(resp, "getProgress")

            progress = json.loads(resp["data"])
            status = progress.get("status")
            if status == _STATUS_DONE:
                return
            if status is None:
                raise RuntimeError(f"讯飞转写进度查询返回异常: {resp}")

            time.sleep(self.poll_interval_seconds)

        raise TimeoutError(f"讯飞转写任务轮询超时: task_id={task_id}")

    def _get_result(self, task_id: str) -> List[Segment]:
        params = self._common_params()
        params.update({"task_id": task_id})
        resp = requests.post(f"{_API_BASE}/getResult", data=params, timeout=30).json()
        self._check_ok(resp, "getResult")

        raw_list = json.loads(resp["data"])
        segments = []
        for item in raw_list:
            bg_ms = int(item.get("bg", 0))
            ed_ms = int(item.get("ed", 0))
            text = item.get("onebest", "")
            segments.append(Segment(start=bg_ms / 1000.0, end=ed_ms / 1000.0, text=text))
        return segments

    @staticmethod
    def _check_ok(resp: dict, step: str) -> None:
        if resp.get("ok") != 0:
            raise RuntimeError(
                f"讯飞 {step} 接口调用失败 [err_no={resp.get('err_no')}]: {resp.get('failed')}"
            )
