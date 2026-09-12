import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

CHUNK_BITRATE = "64k"


@dataclass(frozen=True)
class AudioPart:
    path: Path
    offset_seconds: float


def get_duration_seconds(audio_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


@contextmanager
def convert_audio_parts(
        mp3_path: Path,
        max_file_bytes=30 * 1024 * 1024,
        max_duration_seconds=300
):
    """
    将一个MP3文件进行拆分，先按照 60秒 一个拆分，如果拆分为 60秒后，
    发现文件大小超过30M，那就继续拆分
    """
    if not mp3_path.is_file():
        raise FileNotFoundError(f"找不到 MP3 文件：{str(mp3_path)}")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("未找到 ffmpeg 或 ffprobe，请先安装 FFmpeg。")
    duration = get_duration_seconds(mp3_path)
    if mp3_path.stat().st_size <= max_file_bytes and duration <= max_duration_seconds:
        yield [AudioPart(mp3_path, 0.0)]
        return
    with tempfile.TemporaryDirectory(prefix="whisper_chunks_") as temp_dir:
        temp_path = Path(temp_dir)
        parts: list[AudioPart] = []
        offset = 0.0
        index = 1
        while offset < duration:
            chunk_duration = min(max_duration_seconds, duration - offset)
            chunk_path = temp_path / f"chunk_{index:04}.mp3"

            subprocess.run(
                [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", str(mp3_path),
                    "-ss", str(offset),
                    "-t", str(chunk_duration),
                    "-vn",
                    "-ac", "1",
                    "-ar", "16000",
                    "-c:a", "libmp3lame",
                    "-b:a", CHUNK_BITRATE,
                    str(chunk_path),
                ],
                check=True,
            )

            if chunk_path.stat().st_size > max_file_bytes:
                raise RuntimeError(f"切片仍超过 30MiB：{chunk_path}")

            parts.append(AudioPart(chunk_path, offset))
            offset += chunk_duration
            index += 1

        yield parts


def srt_timestamp(seconds: float) -> str:
    total_ms = round(seconds * 1000)
    hours, total_ms = divmod(total_ms, 3_600_000)
    minutes, total_ms = divmod(total_ms, 60_000)
    secs, milliseconds = divmod(total_ms, 1_000)
    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"


def write_srt(output_path: Path, segments: list[tuple[float, float, str]]) -> None:
    blocks = []

    for index, (start, end, text) in enumerate(segments, start=1):
        cleaned_text = text.strip()
        if cleaned_text:
            blocks.append(
                f"{index}\n"
                f"{srt_timestamp(start)} --> {srt_timestamp(end)}\n"
                f"{cleaned_text}\n"
            )

    output_path.expanduser().resolve().write_text(
        "\n".join(blocks),
        encoding="utf-8",
    )
