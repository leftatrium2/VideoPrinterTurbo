import asyncio
import json
import os.path
import subprocess
from pathlib import Path
from typing import Optional

from pipeline.lip_sync.base import LipSyncBase
from pipeline.lip_sync.fal_latentsync import FalLatentSync
from pipeline.lip_sync.heygen import HeyGen
from pipeline.lip_sync.remote import RemoteLipSync
from pipeline.lip_sync.sync_labs import SyncLabs
from utils import const
from utils.exception import VPTException
import config.config as _config
from fractions import Fraction

from utils.file_utils import get_lip_sync_path


def _get_duration_ms(file_path: str) -> int:
    """获取最长音视频轨的时长，四舍五入到整数毫秒。

    Raises:
        RuntimeError: ffprobe 不可用、执行失败或无法获取有效时长。
    """
    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries",
        "stream=codec_type,duration_ts,time_base,duration",
        "-of", "json",
        "-i", file_path,
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise VPTException("未找到 ffprobe，请确认已安装并加入 PATH", tr=exc) from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"获取媒体时长超时：{file_path}") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"ffprobe 执行失败：{exc.stderr.strip()}"
        ) from exc
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("ffprobe 返回了无效的 JSON") from exc
    durations = []
    for stream in data.get("streams", []):
        if stream.get("codec_type") not in {"video", "audio"}:
            continue
        duration = None
        # 优先使用整数时间戳与时间基准计算。
        try:
            time_base = Fraction(str(stream["time_base"]))
            candidate = int(stream["duration_ts"]) * time_base
            if time_base > 0 and candidate >= 0:
                duration = candidate
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            pass
        # 某些文件不提供 duration_ts，回退到轨道 duration。
        if duration is None:
            try:
                candidate = Fraction(str(stream["duration"]))
                if candidate >= 0:
                    duration = candidate
            except (KeyError, TypeError, ValueError, ZeroDivisionError):
                pass
        if duration is not None:
            durations.append(duration)
    if not durations:
        raise RuntimeError(f"无法获取有效的音视频轨时长：{file_path}")
    duration_ms = max(durations) * 1000
    # 对非负数四舍五入，避免 round() 的银行家舍入行为。
    return (2 * duration_ms.numerator + duration_ms.denominator) // (2 * duration_ms.denominator)


# 音视频的长度，如果长度差超过150ms，那么后续的处理会报错
def _check_video_and_audio_duration(
        video_path: str,
        audio_path: str
) -> tuple[bool, int, int]:
    if not Path(video_path).is_file():
        raise VPTException(const.PIPELINE_ERR_FILE_NOT_FOUND, f"Video file not found: {video_path}")
    if not Path(audio_path).is_file():
        raise VPTException(const.PIPELINE_ERR_FILE_NOT_FOUND, f"Audio file not found: {audio_path}")
    video_duration = _get_duration_ms(video_path)
    audio_duration = _get_duration_ms(audio_path)
    if abs(video_duration - audio_duration) > 150:
        return False, video_duration, audio_duration
    return True, video_duration, audio_duration


def lip_sync(
        video_path: str,
        audio_path: str,
        lip_sync_type: int,
        task_id: str,
        proxy_type: int = const.PROXY_CONFIG_TYPE_UNKNOWN,
        proxy_url: Optional[str] = None,
        **args
) -> Optional[str]:
    # step1. 先检查一下 音视频的长度，如果长度差超过150ms，那么后续的处理会报错
    result, video_duration, autio_duration = _check_video_and_audio_duration(
        video_path=video_path,
        audio_path=audio_path
    )
    if not result:
        raise VPTException(const.PIPELINE_ERR_LIPSYNC_DURATION,
                           f"Video and audio duration mismatch, There must be a difference of 150 ms, video duration: {video_duration}, audio duration: {autio_duration}")
    # step2. 没问题，就开始后面的 唇形同步 处理
    lip_sync: LipSyncBase = None
    if lip_sync_type == const.TASK_CONFIG_LIP_SYNC_REMOTE:
        base_url = args.get("remote_base_url")
        if not base_url:
            raise VPTException(const.PIPELINE_ERR_INVALID_CONFIG, "Remote base URL is not provided")
        lip_sync = RemoteLipSync(
            base_url=base_url
        )
    elif lip_sync_type == const.TASK_CONFIG_LIP_SYNC_FALLATENT:
        api_key = args.get("fal_latent_sync_apikey")
        if not api_key:
            raise VPTException(const.PIPELINE_ERR_INVALID_CONFIG, "Fal Latent Sync API key is not provided")
        lip_sync = FalLatentSync(
            api_key=api_key,
            proxy_url=proxy_url
        )
    elif lip_sync_type == const.TASK_CONFIG_LIP_SYNC_SYNCLABS:
        api_key = args.get("sync_labs_apikey")
        if not api_key:
            raise VPTException(const.PIPELINE_ERR_INVALID_CONFIG, "Sync Labs API key is not provided")
        lip_sync = SyncLabs(
            api_key=api_key,
            proxy_url=proxy_url
        )
    elif lip_sync_type == const.TASK_CONFIG_LIP_SYNC_HEYGEN:
        api_key = args.get("hey_gen_apikey")
        if not api_key:
            raise VPTException(const.PIPELINE_ERR_INVALID_CONFIG, "HeyGen API key is not provided")
        lip_sync = HeyGen(
            api_key=api_key,
            proxy_url=proxy_url
        )

    output_full_path = asyncio.run(get_lip_sync_path())
    if not output_full_path:
        raise VPTException(const.PIPELINE_ERR_INVALID_CONFIG, "storage.lipsync is not configuration")
    output_full_path = os.path.join(output_full_path, f"{task_id}.mp4")
    result = lip_sync.lip_sync(
        video_path,
        audio_path,
        output_path=output_full_path
    )
    if not Path(result).is_file():
        raise VPTException(const.PIPELINE_ERR_FILE_NOT_FOUND, "Lip sync output file does not exist")
    return result


if __name__ == "__main__":
    _config.init_config()
    result = lip_sync(
        video_path="/Users/sunxiao5/Downloads/musetalk/speaker.mp4",
        audio_path="/Users/sunxiao5/Downloads/musetalk/voice_12.200.wav",
        task_id="20261021172733546142",
        lip_sync_type=const.TASK_CONFIG_LIP_SYNC_REMOTE,
        remote_base_url="http://192.168.0.101:8081"
    )
    print(f"result: {result}")
