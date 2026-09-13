import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from pipeline.transcriber.azure_asr.azure_transcriber import AzureASR
from pipeline.transcriber.base import BaseTranscriber
from pipeline.transcriber.bytedance_asr.volcengine_transcriber import VolcengineASR
from pipeline.transcriber.openai_asr.openai_transcriber import OpenAIASR
from pipeline.transcriber.subtitle.subtitle_transcriber import SubTitleTranscriber
from pipeline.transcriber.tencent_asr.tencent_cloud_transcriber import TencentCloudTranscriber
from pipeline.transcriber.whisper_asr.whisper_transcriber import WhisperTranscriber
from pipeline.transcriber.whisper_remote_asr.remote_whisper_transcriber import RemoteWhisperTranscriber
from pipeline.transcriber.xunfei_asr.xf_cloud_asr import XFCloudASR
from pipeline.utils.pipeline_video_downloader_utils import init_downloader
from utils import const
import config.config as _config
from utils.exception import VPTException


def subtitle_convert(
        self,
        url: str,
        lang: int
) -> Optional[str]:
    if not url.strip():
        logging.error("Url is empty")
        return None
    subtitle = SubTitleTranscriber()
    path = subtitle.subtitle(url, lang, self.__proxy)
    return path


def extract_mp3(
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


def asr_convert(
        download_path: str,
        audio_rewrite_type: int,
        **args
) -> Optional[str]:
    if not download_path.strip():
        raise VPTException(const.PIPELINE_ERR_VALUE, "download path is empty")
    video_path = Path(download_path).expanduser().resolve()
    if not video_path.is_file():
        raise VPTException(const.PIPELINE_ERR_FILE_NOT_FOUND, "download path is not exists")
    # 将当前的视频文件，提取音频MP3文件
    mp3_path = Path(video_path).with_suffix(".mp3")
    extract_mp3(video_path, mp3_path)
    # 然后，送到ASR服务中转换成srt
    transcriber: BaseTranscriber = None
    if (audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_LOCAL_WHISPER):
        # local whisper
        local_whisper_type = args.get("local_whisper_type") or 0
        model_size = args.get("model_size") or "large-v3"
        language = args.get("language") or "en"
        transcriber = WhisperTranscriber(
            local_whisper_type=local_whisper_type,
            model_size=model_size,
            language=language
        )
    elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_REMOTE_WHISPER:
        # remote whisper
        remote_whisper_type = args.get("remote_whisper_type") or const.TASK_CONFIG_REMOTE_VLLM_WHISPER
        remote_server_url = args.get("remote_server_url")
        remote_server_model = args.get("remote_server_model")
        language = args.get("language")
        transcriber = RemoteWhisperTranscriber(
            remote_whisper_type=remote_whisper_type,
            remote_server_url=remote_server_url,
            remote_server_model=remote_server_model,
            language=language
        )
        pass
    elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_TENCENT_CLOUD:
        # tencent cloud asr service
        # https://intl.cloud.tencent.com/en/products/asr
        secret_id = args.get("secret_id")
        secret_key = args.get("secret_key")
        app_id = args.get("app_id")
        # 云 API 的公共地域参数
        region = args.get("region")
        # 指定语音识别使用的语言/场景模型，例如中文通用、电话、会议、多方言等。它通常是必填项，不建议依赖“空值默认”。
        # 1. 通用中文普通话、16 kHz 音频：16k_zh（兼容性最稳；旧 SDK 示例的默认值也是它）
        # 2. 需要中英混合、多方言且使用当前大模型 2.0：16k_zh_en_2.0
        # 3. 会议多人转写：16k_zh_en_meeting
        # 4. 实时混元 ASR 内测：Hy-ASR-3.0-preview
        engine_model_type = args.get("engine_model_type") or "16k_zh"
        poll_interval_seconds = 3.0
        poll_timeout_seconds = 600.0,
        transcriber = TencentCloudTranscriber(
            secret_id=secret_id,
            secret_key=secret_key,
            app_id=app_id,
            region=region,
            engine_model_type=engine_model_type,
            poll_interval_seconds=poll_interval_seconds,
            poll_timeout_seconds=poll_timeout_seconds
        )
    elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_XF_YUN:
        # xfyun cloud asr service
        # https://global.xfyun.cn/
        app_id = args.get("app_id")
        api_key = args.get("api_key")
        api_secret = args.get("api_secret")
        language = args.get("language") or "en"
        transcriber = XFCloudASR(
            app_id=app_id,
            api_key=api_key,
            api_secret=api_secret,
            language=language
        )
    elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_AZURE:
        # azure cloud asr
        # https://azure.microsoft.com/en-us
        subscription_key = None
        if args['api_key']:
            subscription_key = args['api_key']
        region = None
        if args['region']:
            region = args['region']
        locales = None
        if args['locales']:
            locales = args['locales']
        enable_diarization = False
        if args['enable_diarization']:
            enable_diarization = args['enable_diarization']
        transcriber = AzureASR(
            subscription_key=subscription_key,
            region=region,
            locales=locales,
            enable_diarization=enable_diarization
        )
    elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_BYTEDANCE:
        # bytedance volcengine asr
        # https://www.volcengine.com/
        app_id = None
        if args['app_id']:
            app_id = args['app_id']
        access_token = None
        if args['access_token']:
            access_token = args['access_token']
        audio_format = "wav"
        if args['audio_format']:
            audio_format = args['audio_format']
        transcriber = VolcengineASR(
            app_id=app_id,
            access_token=access_token,
            audio_format=audio_format
        )
    elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_OPENAI:
        # openai asr
        # https://developers.openai.com/api/docs/guides/speech-to-text
        api_key = None
        if args['api_key']:
            api_key = args['api_key']
        model = "whisper-1"
        if args['model']:
            model = args['model']
        language = None
        if args['language']:
            language = args['language']
        base_url = None
        if args['base_url']:
            base_url = args['base_url']
        transcriber = OpenAIASR(
            api_key=api_key,
            model=model,
            language=language,
            base_url=base_url
        )
    if not transcriber:
        return None
    return transcriber.transcribe(str(mp3_path))


if __name__ == "__main__":
    _config.init_config()
    init_downloader()

    result = asr_convert(
        "/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/downloads/20260720215545133997.mp4",
        audio_rewrite_type=const.TASK_CONFIG_ASR_FROM_REMOTE_WHISPER,
        remote_whisper_type=const.TASK_CONFIG_REMOTE_WHISPER_CPP,
        remote_server_url="http://192.168.0.105:8004/inference",
        language="en"
    )
