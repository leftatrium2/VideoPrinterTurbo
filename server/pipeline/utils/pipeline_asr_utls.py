import asyncio
import logging
import os.path
from pathlib import Path
from typing import Optional

from pipeline.separate_vocals.separate_vocals import SeparateVocals
from pipeline.transcriber.azure_asr.azure_transcriber import AzureASR
from pipeline.transcriber.base import BaseTranscriber
from pipeline.transcriber.bytedance_asr.volcengine_transcriber import VolcengineASR
from pipeline.transcriber.openai_asr.openai_transcriber import OpenAIASR
from pipeline.transcriber.subtitle.subtitle_transcriber import SubTitleTranscriber
from pipeline.transcriber.tencent_asr.tencent_cloud_transcriber import TencentCloudTranscriber
from pipeline.transcriber.whisper_asr.whisper_transcriber import WhisperTranscriber
from pipeline.transcriber.whisper_remote_asr.remote_whisper_transcriber import RemoteWhisperTranscriber
from pipeline.transcriber.xunfei_asr.xf_cloud_asr import XFCloudASR
from utils import const
from utils.exception import VPTException
from utils.file_utils import get_subtitle_path, get_separate_vocals_path

logger = logging.getLogger(__name__)


def audio_separate(
        src_mp3_path: str
):
    audio_separator_path = asyncio.run(get_separate_vocals_path())
    separate_vocals = SeparateVocals(
        src_mp3_path=src_mp3_path,
        dst_mp3_dir=audio_separator_path if audio_separator_path else ""
    )
    return separate_vocals.convert()


def subtitle_convert(
        url: str,
        lang: int,
        task_id: str,
        proxy_type: int = const.PROXY_CONFIG_TYPE_UNKNOWN,
        proxy_url: Optional[str] = None
) -> Optional[str]:
    if not url.strip():
        logger.error("Url is empty")
        return None
    subtitle_path = asyncio.run(get_subtitle_path())
    if not subtitle_path:
        raise VPTException(const.PIPELINE_ERR_FILE_NOT_FOUND, "config.yaml not set storage.subtitle!")
    srt_full_path = os.path.join(subtitle_path, f"{task_id}.srt")
    subtitle = SubTitleTranscriber()
    path = subtitle.subtitle(url, lang, srt_full_path, proxy_url)
    return path


def asr_convert(
        download_path: str,
        audio_rewrite_type: int,
        proxy_type: int = const.PROXY_CONFIG_TYPE_UNKNOWN,
        proxy_url: Optional[str] = None,
        **args
) -> Optional[str]:
    if not download_path.strip():
        raise VPTException(const.PIPELINE_ERR_VALUE, "download path is empty")
    audio_path = Path(download_path).expanduser().resolve()
    if not audio_path.is_file():
        raise VPTException(const.PIPELINE_ERR_FILE_NOT_FOUND, "download path is not exists")
    if audio_path.suffix.lower() != ".mp3":
        raise VPTException(const.PIPELINE_ERR_FILE_NOT_AUDIO_FORMAT, "download path is not mp3 format")
    # 然后，送到ASR服务中转换成srt
    transcriber: BaseTranscriber = None
    if (audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_LOCAL_WHISPER):
        # local whisper
        local_whisper_type = args.get("local_whisper_type") or 0
        model_size = args.get("model_size") or "large-v3"
        language = args.get("language")
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
        secret_id = args.get("secret_id") or ""
        secret_key = args.get("secret_key") or ""
        app_id = args.get("app_id") or ""
        # 云 API 的公共地域参数
        region = args.get("region") or ""
        # 指定语音识别使用的语言/场景模型，例如中文通用、电话、会议、多方言等。它通常是必填项，不建议依赖“空值默认”。
        # 1. 通用中文普通话、16 kHz 音频：16k_zh（兼容性最稳；旧 SDK 示例的默认值也是它）
        # 2. 需要中英混合、多方言且使用当前大模型 2.0：16k_zh_en_2.0
        # 3. 会议多人转写：16k_zh_en_meeting
        # 4. 实时混元 ASR 内测：Hy-ASR-3.0-preview
        engine_model_type = args.get("engine_model_type") or "16k_zh"
        poll_interval_seconds = 3.0
        poll_timeout_seconds = 600.0
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
        app_id = args.get("app_id") or ""
        web_api = args.get("web_api") or ""
        api_secret = args.get("api_secret") or ""
        language = args.get("language")
        transcriber = XFCloudASR(
            app_id=app_id,
            web_api=web_api,
            api_secret=api_secret,
            language=language
        )
    elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_AZURE:
        # azure cloud asr
        # https://azure.microsoft.com/en-us
        subscription_key = args.get("api_key") or ""
        region = args.get("region") or ""
        locales = args.get("locales")
        enable_diarization = args.get("enable_diarization") or False
        transcriber = AzureASR(
            subscription_key=subscription_key,
            region=region,
            locales=locales,
            enable_diarization=enable_diarization
        )
    elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_BYTEDANCE:
        # bytedance volcengine asr
        # https://www.volcengine.com/
        app_id = args.get("app_id") or ""
        access_token = args.get("access_token") or ""
        audio_format = args.get("audio_format") or "mp3"
        transcriber = VolcengineASR(
            app_id=app_id,
            access_token=access_token,
            audio_format=audio_format
        )
    elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_OPENAI:
        # openai asr
        # https://developers.openai.com/api/docs/guides/speech-to-text
        api_key = args.get('api_key') or ""
        model = args.get("model") or "whisper-1"
        language = args.get("language")
        base_url = args.get("base_url")
        transcriber = OpenAIASR(
            api_key=api_key,
            model=model,
            base_url=base_url,
            language=language
        )
    if not transcriber:
        return None
    transcriber.config(proxy=proxy_url)
    return transcriber.transcribe(download_path)
