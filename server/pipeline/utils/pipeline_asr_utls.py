import logging
import os
from typing import Optional

from pipeline.transcriber.azure_asr.azure_transcriber import AzureASR
from pipeline.transcriber.base import BaseTranscriber
from pipeline.transcriber.bytedance_asr.volcengine_transcriber import VolcengineASR
from pipeline.transcriber.openai_asr.openai_transcriber import OpenAIASR
from pipeline.transcriber.subtitle.subtitle_transcriber import SubTitleTranscriber
from pipeline.transcriber.tencent_asr.tencent_cloud_transcriber import TencentCloudTranscriber
from pipeline.transcriber.whisper_asr.whisper_transcriber import WhisperTranscriber
from pipeline.transcriber.xunfei_asr.xf_cloud_asr import XFCloudASR
from pipeline.utils.pipeline_video_downloader_utils import init_downloader
from utils import const
import config.config as _config


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


def asr_convert(
        download_path: str,
        **args
) -> Optional[str]:
    if not download_path.strip():
        logging.error("download path is empty")
        return None
    if not os.path.exists(download_path):
        logging.error("download path is not exists")
        return None
    if not args['audio_rewrite_type']:
        logging.error("audio rewrite type is empty")
        return None
    audio_rewrite_type = args['audio_rewrite_type']
    transcriber: BaseTranscriber = None
    if (audio_rewrite_type == const.TASK_CONFIG_ASR_FASTER_WHISPER
            or audio_rewrite_type == const.TASK_CONFIG_ASR_MLX_WHISPER
            or audio_rewrite_type == const.TASK_CONFIG_ASR_OPENAI_WHISPER):
        # local whisper
        model_size = "large-v3"
        if args['model_size']:
            model_size = args['model_size']
        language = None
        if args['language']:
            language = args['language']
        transcriber = WhisperTranscriber(
            local_whisper_type=audio_rewrite_type,
            model_size=model_size,
            language=language
        )
    elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_TENCENT_CLOUD:
        # tencent cloud asr service
        # https://intl.cloud.tencent.com/en/products/asr
        secret_id = None
        if args['secret_id']:
            secret_id = args['secret_id']
        secret_key = None
        if args['secret_key']:
            secret_key = args['secret_key']
        app_id = None
        if args['app_id']:
            app_id = args['app_id']
        region = None
        if args['region']:
            region = args['region']
        engine_model_type = None
        if args['engine_model_type']:
            engine_model_type = args['engine_model_type']
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
        app_id = None
        if args['app_id']:
            app_id = args['app_id']
        api_key = None
        if args['api_key']:
            api_key = args['api_key']
        api_secret = None
        if args['api_secret']:
            api_secret = args['api_secret']
        language = None
        if args['language']:
            language = args['language']
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
    return transcriber.transcribe(download_path)


if __name__ == "__main__":
    _config.init_config()
    init_downloader()
    result = asr_convert("/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/downloads/20260720215545133997.mp4")