import json
import logging
import os
import shutil
import subprocess
import tempfile
from typing import List, Optional

from pipeline.transcriber.asr_exception import ASRException
from pipeline.transcriber.segment import Segment

logger = logging.getLogger(__name__)


def _check_binary(name: str) -> None:
    if shutil.which(name) is None:
        raise ASRException(
            f"未找到可执行文件 `{name}`，请先安装 ffmpeg（含 ffprobe）并确保其在 PATH 中。"
        )


def get_file_size(audio_path: str) -> int:
    """返回文件大小（字节）"""
    return os.path.getsize(audio_path)


def format_timestamp(seconds: float) -> str:
    """将秒数格式化为 SRT 时间戳: HH:MM:SS,mmm"""
    if seconds < 0:
        seconds = 0
    total_ms = round(seconds * 1000)
    hours, remainder_ms = divmod(total_ms, 3_600_000)
    minutes, remainder_ms = divmod(remainder_ms, 60_000)
    secs, ms = divmod(remainder_ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def segments_to_srt(segments: List[Segment]) -> str:
    """
    将句子级 Segment 列表转换为标准 SRT 文本。
    - 过滤空文本
    - 按 start 时间排序，防止分片拼接后顺序错乱
    - 保证 end > start，避免时间戳异常导致播放器解析失败
    """
    cleaned = [s for s in segments if s.text and s.text.strip()]
    cleaned.sort(key=lambda s: s.start)

    lines = []
    for idx, seg in enumerate(cleaned, start=1):
        start = seg.start
        end = seg.end if seg.end > seg.start else seg.start + 0.5
        lines.append(str(idx))
        lines.append(f"{format_timestamp(start)} --> {format_timestamp(end)}")
        lines.append(seg.text.strip())
        lines.append("")  # 空行分隔

    return "\n".join(lines).strip() + "\n"


def get_duration_seconds(audio_path: str) -> float:
    """使用 ffprobe 探测音频时长（秒）"""
    _check_binary("ffprobe")
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        audio_path,
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        data = json.loads(out.decode("utf-8"))
        return float(data["format"]["duration"])
    except Exception as e:
        raise ASRException(f"探测音频时长失败: {e}") from e


def cleanup_dir(path: str) -> None:
    """清理临时目录，异常也不向外抛出"""
    try:
        if path and os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
    except Exception as e:
        logger.warning(f"清理临时目录失败: {path}, {e}")


def convert_audio(
        audio_path: str,
        out_path: str,
        sample_rate: int = 16000,
        channels: int = 1,
        audio_format: str = "wav",
) -> str:
    """
    使用 ffmpeg 将音频转换为指定采样率/声道/格式，用于满足各云服务对音频格式的要求。
    """
    _check_binary("ffmpeg")
    cmd = [
        "ffmpeg", "-y",
        "-i", audio_path,
        "-ar", str(sample_rate),
        "-ac", str(channels),
        "-f", audio_format,
        out_path,
    ]
    try:
        subprocess.run(
            cmd, check=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode("utf-8", errors="ignore") if e.stderr else str(e)
        raise ASRException(f"ffmpeg 转码失败: {stderr}") from e
    return out_path


def split_audio_by_duration(
        audio_path: str,
        chunk_seconds: int,
        out_dir: str = None,
        sample_rate: int = 16000,
        channels: int = 1,
        audio_format: str = "wav",
) -> List[str]:
    """
    按固定时长将音频切分为多个分片文件（切分的同时统一转码，保证每片格式合规）。
    返回按时间顺序排列的分片文件路径列表。
    """
    _check_binary("ffmpeg")
    if out_dir is None:
        out_dir = tempfile.mkdtemp(prefix="asr_split_")
    else:
        os.makedirs(out_dir, exist_ok=True)

    pattern = os.path.join(out_dir, f"chunk_%04d.{audio_format}")
    cmd = [
        "ffmpeg", "-y",
        "-i", audio_path,
        "-ar", str(sample_rate),
        "-ac", str(channels),
        "-f", "segment",
        "-segment_time", str(chunk_seconds),
        "-reset_timestamps", "1",
        pattern,
    ]
    try:
        subprocess.run(
            cmd, check=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode("utf-8", errors="ignore") if e.stderr else str(e)
        raise ASRException(f"ffmpeg 分片失败: {stderr}") from e

    chunks = sorted(
        os.path.join(out_dir, f) for f in os.listdir(out_dir)
        if f.startswith("chunk_") and f.endswith(f".{audio_format}")
    )
    if not chunks:
        raise ASRException("音频分片失败：未生成任何分片文件")
    return chunks


def build_proxies(proxy: Optional[str]) -> Optional[dict]:
    """
    将单个代理地址（如 "http://127.0.0.1:7890"）转换为 requests 库所需的 proxies 字典。
    http/https 请求统一走同一个代理地址；不传 proxy 则返回 None（不使用代理）。
    """
    if not proxy:
        return None
    return {"http": proxy, "https": proxy}
