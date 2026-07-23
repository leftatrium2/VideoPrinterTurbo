import importlib
import logging
import os.path

from sqlalchemy import select

import config.config as _config
from models.model import VptTask
from pipeline.downloader.base import DownloaderContext, BaseDownloader
from pipeline.downloader.yt_dlp.yt_dlp_downloader import YtDlpDownloader
from pipeline.llm.base import BaseLLMProvider
from pipeline.llm.openai_provider import OpenAIProvider
from pipeline.material.base import BaseMaterialSearcher
from pipeline.transcriber.aliyun_asr.aliyun_transcriber import AliyunASR
from pipeline.transcriber.azure_asr.azure_transcriber import AzureASR
from pipeline.transcriber.base import BaseTranscriber
from pipeline.transcriber.bytedance_asr.volcengine_transcriber import VolcengineASR
from pipeline.transcriber.openai_asr.openai_transcriber import OpenAIASR
from pipeline.transcriber.subtitle.subtitle_transcriber import SubTitleTranscriber
from pipeline.transcriber.tencent_asr.tencent_cloud_transcriber import TencentCloudTranscriber
from pipeline.transcriber.whisper_asr.whisper_transcriber import WhisperTranscriber
from pipeline.transcriber.xunfei_asr.xf_cloud_asr import XFCloudASR
from pipeline.tts.azure_tts_v1 import AzureTTSV1
from pipeline.tts.base import TTSBase
from pipeline.tts.google_gemini_tts import GoogleGeminiTTS
from utils import const
from utils.database import database

downloaders = {}


def init_downloader():
    global downloaders
    for k, v in _config.downloader_config.items():
        v = v.strip()
        module_path, class_name = v.rsplit(".", 1)
        cls = getattr(importlib.import_module(module_path), class_name)
        downloaders[k] = cls()
    downloaders['others'] = YtDlpDownloader()


def get_downloader(url: str) -> BaseDownloader or None:
    if not url:
        return None
    for k, v in _config.downloader_config.items():
        keyword = k.lower().strip()
        if keyword in url:
            if k not in downloaders:
                logging.error("cant find the downloader, maybe it not init, keyword: ", k)
                return None
            return downloaders[k]

    return downloaders['others']


class Pipeline:

    def __init__(self):
        self.__proxy = None

    def set_proxy(self, proxy: str):
        self.__proxy = proxy

    # Check if the video URL is downloadable
    def check(
            self,
            url: str
    ) -> bool:
        if not url.strip():
            logging.error("Url is empty")
            return False
        downloader = get_downloader(url)
        if not downloader:
            logging.error("Downloader is None")
            return False
        return downloader.check(url, self.__proxy)

    # 1. Download video
    def download(
            self,
            url: str,
            output_dir: str,
            ctx: DownloaderContext,
            is_download_proxy: bool = True
    ) -> str or None:
        if not url.strip():
            logging.error("Url is empty")
            return None
        downloader = get_downloader(url)
        if not downloader:
            logging.error("Downloader is None")
            return None
        if is_download_proxy:
            return downloader.download(url, output_dir, ctx, self.__proxy)
        return downloader.download(url, output_dir, ctx)

    # 2. Audio to text (subtitle)
    def subtitle(
            self,
            url: str,
            lang: int
    ) -> str or None:
        if not url.strip():
            logging.error("Url is empty")
            return None
        subtitle = SubTitleTranscriber()
        path = subtitle.subtitle(url, lang, self.__proxy)
        return path

    # 2. Audio to text (ASR)
    def transcribe(
            self,
            download_path: str,
            **args
    ) -> str or None:
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
        if audio_rewrite_type == const.TASK_CONFIG_ASR_FASTER_WHISPER or audio_rewrite_type == const.TASK_CONFIG_ASR_MLX_WHISPER or audio_rewrite_type == const.TASK_CONFIG_ASR_OPENAI_WHISPER:
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
        elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_ALIYUN:
            # aliyun cloud asr
            # https://www.alibabacloud.com/help/en/model-studio/qwen-asr-api-reference?scm=20140722.S_help%40%40%E6%96%87%E6%A1%A3%40%402986952._.RL_asr-LOC_2024NSHelpLink-OR_ser-PAR1_0bc3b4b317846037013694282e5ff8-V_4-P0_0-P1_0
            api_key = None
            if args['api_key']:
                api_key = args['api_key']
            model = "paraformer-v2"
            if args['model']:
                model = args['model']
            transcriber = AliyunASR(
                api_key=api_key,
                model=model
            )
            pass
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

    # 3. LLM rewrite
    def rewrite(self, text: str, src_path: str, dst_path: str,
                config: dict) -> bool:
        if 'api_key' not in config or 'base_url' not in config or 'model' not in config:
            return False
        llm: BaseLLMProvider = OpenAIProvider()
        api_key = config['api_key']
        base_url = config['base_url']
        model = config['model']
        llm.config(api_key, base_url, model)
        llm.rewrite(text, src_path, dst_path)
        return True

    # 4. Output to speech
    # If the original video has an audio track, selecting this option will remove the original audio and use the new TTS voice instead
    def text_to_speech(self, tts_engine: str, subtitle_path: str, lang: str, voice: str, api_key: str = None,
                       region: str = None, proxy: str = None) -> bool:
        tts: TTSBase = None
        if tts_engine == "Azure TTS V1":
            tts = AzureTTSV1()
        elif tts_engine == "Google Gemini TTS":
            tts = GoogleGeminiTTS()
        if not tts:
            return False
        tts.config(api_key=api_key, region=region, proxy=proxy)
        tts.rewrite(subtitle_path, lang, voice)
        return True

    # 7. Video overlay
    def video_overlay(self) -> bool:
        video_searcher: BaseMaterialSearcher = None
        # 7.1 先搜索
        # 7.2 根据搜索拿到的素材，下载
        return True

    # 8. Publish (not yet implemented)
    def publish(self) -> bool:
        return True


pipeline = Pipeline()


def main():
    task_id = "20260701212108501553"
    database.start()
    db = database.get_sync_session()
    result = db.execute(select(VptTask).where(
        VptTask.task_id == task_id,
        VptTask.is_deleted == 0
    ).order_by(VptTask.create_time.asc()).limit(1))
    item = result.scalar_one_or_none()
    print(item)


if __name__ == "__main__":
    main()
