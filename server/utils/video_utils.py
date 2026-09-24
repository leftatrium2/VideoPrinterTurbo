import json
import shutil
import subprocess
from pathlib import Path

import config.config as _config
from utils import const
from utils.exception import VPTException
from utils.file_utils import get_current_path


def _check_binary(name: str) -> None:
    if shutil.which(name) is None:
        raise VPTException(const.PIPELINE_ERR_FILE_NOT_FOUND,
                           f"未找到可执行文件 `{name}`，请先安装 ffmpeg（含 ffprobe）并确保其在 PATH 中。")


def convert_video_to_mp3(
        video_path: Path,
        mp3_path: Path
) -> None:
    if not video_path.is_file():
        raise FileNotFoundError(f"video path does not exists, video path: {video_path}")
    if not shutil.which("ffmpeg"):
        raise RuntimeError("未找到 ffmpeg，请先安装 FFmpeg。")
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", str(video_path),
                "-map", "0:a:0",  # 取第一条音频轨
                "-vn",  # 不输出视频
                "-ac", "1",  # 单声道，适合语音识别
                "-ar", "16000",  # 16kHz，适合 Whisper
                "-c:a", "libmp3lame",
                "-b:a", "64k",
                str(mp3_path),
            ],
            check=True,
            timeout=600,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as ex:
        # FFmpeg 返回非 0 退出码
        raise VPTException(const.PIPELINE_ERR_SUBPROCESS_NONE_ZERO, f"""
        cmd: {ex.cmd}
        return code: {ex.returncode}
        stdout: {ex.stdout}
        stderr: {ex.stderr}
        """)
    except FileNotFoundError as ex:
        raise VPTException(const.PIPELINE_ERR_FILE_NOT_FOUND, "path is not exists")
    except subprocess.TimeoutExpired as ex:
        raise VPTException(const.PIPELINE_ERR_TIMEOUT_EXPIRED, "timeout_expired")


def get_video_or_audio_duration(path: str):
    real_path = Path(path).expanduser().resolve()
    if not real_path.is_file():
        raise VPTException(const.PIPELINE_ERR_FILE_NOT_FOUND, f"cant find the video&audio file, path: {str(real_path)}")
    """使用 ffprobe 探测音频时长（秒）"""
    _check_binary("ffprobe")
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(real_path),
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        data = json.loads(out.decode("utf-8"))
        return float(data["format"]["duration"])
    except Exception as e:
        raise VPTException(const.PIPELINE_ERR_FFPROBE_DURATION, f"探测音频时长失败: {e}", tr=e) from e


def get_video_width_height(path: str):
    real_path = Path(path).expanduser().resolve()
    if not real_path.is_file():
        raise VPTException(const.PIPELINE_ERR_FILE_NOT_FOUND, f"cant find the video&audio file, path: {str(real_path)}")
    """使用 ffprobe 探测音频时长（秒）"""
    _check_binary("ffprobe")
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json",
        str(real_path)
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        streams = data.get("streams")
        return streams[0].get("width"), streams[0].get("height")
    except Exception as ex:
        raise VPTException(const.PIPELINE_ERR_FFPROBE_WIDTH_HEIGHT, f"ffprobe run error, error :{ex}", tr=ex) from ex


if __name__ == "__main__":
    _config.init_config()
    path = get_current_path()
    uploaded_video_path = Path(path).joinpath("storage/downloads/4e047a00eaa248c896dbc4b50fd7eb9f.webm")
    # duration_sec = get_video_or_audio_duration(str(uploaded_video_path))
    # print(duration_sec)
    width, height = get_video_width_height(str(uploaded_video_path))
    print(width, height)
