import asyncio
import importlib
import json
import logging
import os.path
import re
from pathlib import Path
from typing import Optional

from openai import OpenAI
from sqlalchemy import select

import config.config as _config
from config.config import init_config
from models.model import VptTask, VptLlmConfig
from pipeline.downloader.base import DownloaderContext, BaseDownloader
from pipeline.downloader.yt_dlp.yt_dlp_downloader import YtDlpDownloader
from pipeline.llm.base import BaseLLMProvider
from pipeline.llm.openai_provider import OpenAIProvider
from pipeline.material.base import BaseMaterialSearcher, VideoAspect
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
from utils.file_utils import get_material_path

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


class PipelineManager:

    def __init__(self):
        self.__proxy = None
        self.__data = {}

    def set_proxy(self, proxy: str):
        self.__proxy = proxy

    def init(self):
        self.__data = {}

    def get_data(self) -> dict:
        return self.__data

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

    TIMESTAMP_RE = re.compile(
        r"^\d{1,2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*"
        r"\d{1,2}:\d{2}:\d{2}[,.]\d{3}"
    )

    def read_subtitle_text(self, subtitle_file: str | Path) -> str:
        """读取 SRT、VTT 或每行一句的纯文本字幕，去除序号和时间轴。"""
        raw = Path(subtitle_file).read_text(encoding="utf-8-sig")

        subtitle_lines = []
        for line in raw.splitlines():
            line = line.strip()

            if (
                    not line
                    or line == "WEBVTT"
                    or line.isdigit()
                    or self.TIMESTAMP_RE.match(line)
                    or line.startswith(("NOTE", "STYLE", "REGION"))
            ):
                continue

            # 去掉 VTT/HTML 标签，如 <i>、<c.color>
            line = re.sub(r"<[^>]+>", "", line)

            # 去除相邻重复字幕
            if not subtitle_lines or subtitle_lines[-1] != line:
                subtitle_lines.append(line)

        return " ".join(subtitle_lines)

    def get_material_keyword_from_llm(self, text_file_path: str) -> Optional[list]:
        if not os.path.exists(text_file_path):
            logging.error(f"{text_file_path} is not exists")
            return None
        subtitle_text = self.read_subtitle_text(text_file_path)
        db = database.get_sync_session()
        result = db.execute(select(VptLlmConfig).limit(1))
        item = result.scalar_one_or_none()
        if not item:
            logging.error(
                f"LLM is not configured to extract search keywords from the subtitles of the current video footage.")
            return None
        api_key = item.api_key
        base_url = item.base_url
        if not api_key or not base_url:
            logging.error(
                f"LLM configure is not correct. api key: {api_key} or base_url: {base_url} not set")
            return None
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        amount = 5
        model = "gpt-5.5"
        if item.llm_model_name:
            model = item.llm_model_name
        system_prompt = """
  你是一个视频素材搜索词生成器。

  任务：根据用户提供的视频字幕，生成适合 Pexels、Pixabay 等素材网站使用的英文搜索词。

  规则：
  1. 只返回 JSON 字符串数组，不要 Markdown，不要解释。
  2. 每个搜索词包含 1 至 4 个英文单词。
  3. 搜索词应对应可视觉化的内容：人物、动作、物品、场景、环境或情绪。
  4. 覆盖字幕中的不同重点，避免语义重复。
  5. 优先使用可在视频素材网站中实际搜索到的具体表达。
  """.strip()
        user_prompt = f"""
  请基于以下字幕生成 {amount} 个英文视频素材搜索词：

  <subtitle>
  {subtitle_text}
  </subtitle>
  """.strip()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )
        text = response.choices[0].message.content.strip()
        # 即使模型意外附带说明，也尽量提取 JSON 数组
        match = re.search(r"\[[\s\S]*\]", text)
        if not match:
            logging.error(f"模型未返回 JSON 数组：{text}")
            return None
        terms = json.loads(match.group())
        if not isinstance(terms, list) or not all(isinstance(term, str) for term in terms):
            logging.error(f"模型返回格式错误：{text}")
            return None
        return terms

    # 7. Video overlay
    def video_overlay(
            self,
            subtitle_file_path: str,
            material_keyword: str = Optional[str],
            material_splicing_mode: int = 0,
            material_transition_mode: int = 0,
            material_video_ratio: int = 0,
            material_max_duration: int = 0,
            material_generate_count: int = 0
    ) -> bool:
        video_searcher: BaseMaterialSearcher = None
        material_path = asyncio.run(get_material_path())
        keyword_list = []
        # 如果用户设置了搜索关键字，那么优先使用此关键字搜索
        if material_keyword:
            keyword_list = material_keyword.split(' ')
        else:
            # 如果没有找到搜索关键字，那么从当前的字幕（ASR导出的也算）
            keyword_list = self.get_material_keyword_from_llm(subtitle_file_path)
            if not keyword_list:
                logging.error("No keyword found")
                return False
        # 7.1 先搜索
        video_aspect = VideoAspect.portrait
        if material_video_ratio == 1:
            video_aspect = VideoAspect.portrait
        elif material_video_ratio == 2:
            video_aspect = VideoAspect.landscape
        material_info_list = video_searcher.search(keyword_list, video_aspect, material_max_duration)
        # 7.2 根据搜索拿到的素材，下载
        if material_info_list:
            self.__data['material'] = []
            for material_info in material_info_list:
                full_file_path = video_searcher.download(material_info, material_path)
                material_dict = {
                    "file_path": full_file_path,
                    "duration": material_info.duration,
                    "aspect": video_aspect.value,
                    "provider": material_info.provider,
                    "url": material_info.url
                }
                self.__data['material'].append(material_dict)
        return True

    # 8. Publish (not yet implemented)
    def publish(self) -> bool:
        return True


pipeline = PipelineManager()

if __name__ == "__main__":
    init_config()
    task_id = "20260727215533153521"
    database.start()
    db = database.get_sync_session()
    result = db.execute(select(VptTask).where(
        VptTask.task_id == task_id,
        VptTask.is_deleted == 0
    ).order_by(VptTask.create_time.asc()).limit(1))
    item = result.scalar_one_or_none()
    if item:
        result = pipeline.get_material_keyword_from_llm(
            "/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/video_to_text/Give Me 9 Minutes, I'll Make You AI-Native.srt")
        print(result)
