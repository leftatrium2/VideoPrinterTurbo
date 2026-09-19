import asyncio
import json
import logging
import os
import shutil
import subprocess
import tempfile
from typing import List, Optional

from pipeline.transcriber.segment import Segment
from utils import const
from utils.exception import VPTException
from utils.file_utils import get_video_to_text_path
from utils.video_utils import _check_binary

logger = logging.getLogger(__name__)


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
        raise VPTException(const.PIPELINE_ERR_FFPROBE_DURATION, f"探测音频时长失败: {e}", tr=e) from e


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
        raise VPTException(const.PIPELINE_ERR_FFMPEG_TRANSCRIBER, f"ffmpeg 转码失败: {stderr}", tr=e) from e
    return out_path


def split_audio_by_duration(
        audio_path: str,
        chunk_seconds: int,
        out_dir: Optional[str] = None,
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
        raise VPTException(const.PIPELINE_ERR_ASR_SEGMENTS, f"ffmpeg 分片失败: {stderr}") from e

    chunks = sorted(
        os.path.join(out_dir, f) for f in os.listdir(out_dir)
        if f.startswith("chunk_") and f.endswith(f".{audio_format}")
    )
    if not chunks:
        raise VPTException(const.PIPELINE_ERR_ASR_SEGMENTS, "音频分片失败：未生成任何分片文件")
    return chunks


def save_to_srt(asr_text: str, audio_path: str) -> Optional[str]:
    try:
        asr_path = asyncio.run(get_video_to_text_path())
        if asr_path:
            from pathlib import Path
            asr_file_name = Path(audio_path).stem
            asr_full_file_name = f"{asr_file_name}.srt"
            asr_full_path = os.path.join(asr_path, asr_full_file_name)
            with open(asr_full_path, "w", encoding="utf-8") as f:
                f.write(asr_text)
            return asr_full_path
    except Exception as e:
        logger.warning(f"保存 SRT 文件失败: {e}")
        return None
