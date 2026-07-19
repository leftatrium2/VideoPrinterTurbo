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
from pipeline.transcriber.base import BaseTranscriber
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
    __proxy = None

    def __init__(self):
        pass

    def set_proxy(self, proxy: str):
        self.__proxy = proxy

    # Check if the video URL is downloadable
    def check(self, url: str) -> bool:
        if not url.strip():
            logging.error("Url is empty")
            return False
        downloader = get_downloader(url)
        if not downloader:
            logging.error("Downloader is None")
            return False
        return downloader.check(url, self.__proxy)

    # 1. Download video
    def download(self, url: str, output_dir: str, ctx: DownloaderContext) -> str or None:
        if not url.strip():
            logging.error("Url is empty")
            return None
        downloader = get_downloader(url)
        if not downloader:
            logging.error("Downloader is None")
            return None
        return downloader.download(url, output_dir, ctx, self.__proxy)

    # 2. Audio to text (subtitle)
    def subtitle(self, url: str, lang: int) -> str or None:
        if not url.strip():
            logging.error("Url is empty")
            return None
        subtitle = SubTitleTranscriber()
        path = subtitle.subtitle(url, lang, self.__proxy)
        return path

    # 2. Audio to text (ASR)
    def transcribe(self, download_path: str, audio_rewrite_type: int) -> str or None:
        if not download_path.strip():
            logging.error("download path is empty")
            return None
        if not os.path.exists(download_path):
            logging.error("download path is not exists")
            return None
        transcriber: BaseTranscriber = None
        if audio_rewrite_type == const.TASK_CONFIG_ASR_FASTER_WHISPER or audio_rewrite_type == const.TASK_CONFIG_ASR_MLX_WHISPER or audio_rewrite_type == const.TASK_CONFIG_ASR_OPENAI_WHISPER:
            transcriber = WhisperTranscriber()
        elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_TENCENT_CLOUD:
            transcriber = TencentCloudTranscriber()
        elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_XF_YUN:
            transcriber = XFCloudASR()
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
