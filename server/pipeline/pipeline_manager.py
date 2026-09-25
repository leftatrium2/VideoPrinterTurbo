import asyncio
import logging
from pathlib import Path
from typing import Optional

from sqlalchemy import select

import utils.logger  # noqa: F401  # 确保 logging.basicConfig 在最早执行
from config.config import init_config
from models.model import VptTasks, VptAsrConfig, VptLlmConfig, VptTtsConfig
from pipeline.bean.pipeline_data import PipeLineData
from pipeline.bean.video_downloader_bean import VideoDownloaderBean
from pipeline.downloader.base import DownloaderContext
from pipeline.utils.pipeline_asr_utls import asr_convert, subtitle_convert
from pipeline.utils.pipeline_llm_utils import llm_rewrite
from pipeline.utils.pipeline_material_video_utils import video_overlay
from pipeline.utils.pipeline_tts_utils import tts_from_subtitle
from pipeline.utils.pipeline_video_downloader_utils import check_video, download_video, init_downloader
from utils import const
from utils.database import database
from utils.exception import VPTException
from utils.file_utils import get_current_path, get_llm_rewrite_path, get_relative_path, get_absolute_path, \
    get_tts_rewrite_path, get_resource_font_path
from utils.video_utils import get_video_width_height, get_video_or_audio_duration
from utils.tts_voice import get_lang_from_voice

logger = logging.getLogger(__name__)


class PipelineManager:

    def __init__(self):
        self.__proxy = None
        self.__data: PipeLineData = PipeLineData()
        self.inner_downloader_context = PipelineManager.InnerDownloaderContext()

    class InnerDownloaderContext(DownloaderContext):

        def on_create(self, url: str):
            logger.info(f"on_create: url: {url}")

        def on_start(self, url: str):
            logger.info(f"on_start: url: {url}")

        def on_progress(self, url: str, codec_type: int, progress: float):
            logger.info(f"on_progress: url: {url}, codec_type: {codec_type}, progress: {progress}")

        def on_complete(self, url: str):
            logger.info(f"on_complete: url: {url}")

        def on_error(self, url: str, error: Exception):
            logger.info(f"on_error: url: {url}, error: {error}")

    def set_proxy(self, proxy: str):
        self.__proxy = proxy

    def get_data(self) -> Optional[PipeLineData]:
        return self.__data

    def init(self):
        self.__data = PipeLineData()

    @staticmethod
    def __update_db_task(task: VptTasks):
        db = database.get_sync_session()
        result = db.execute(select(VptTasks).where(
            VptTasks.task_id == task.task_id,
            VptTasks.is_deleted == 0
        ))
        item = result.scalar_one_or_none()
        if not item:
            logger.error(f"task not found: {task.task_id}")
            return
        item.task_status = task.task_status
        item.error_code = task.error_code
        item.error_desc = task.error_desc
        item.task_message = task.task_message
        item.pipeline_status = task.pipeline_status
        item.task_upload_video_path = task.task_upload_video_path
        item.task_original_video_path = task.task_original_video_path
        db.commit()
        db.refresh(item)

    @staticmethod
    def __get_asr_config():
        asr_config_db = database.get_sync_session()
        asr_config_result = asr_config_db.execute(select(VptAsrConfig).limit(1))
        asr_config_item = asr_config_result.scalar_one_or_none()
        if not asr_config_item:
            raise VPTException(const.PIPELINE_ERR_ASR_NOT_CONFIGURATION, "asr config not found")
        return asr_config_item

    @staticmethod
    def __get_llm_config():
        llm_config_db = database.get_sync_session()
        llm_config_result = llm_config_db.execute(select(VptLlmConfig).limit(1))
        llm_config_item = llm_config_result.scalar_one_or_none()
        if not llm_config_item:
            raise VPTException(const.PIPELINE_ERR_LLM_CONFIG, "llm config not found")
        return llm_config_item

    def __update_pipeline_status(self, task: VptTasks, pipeline_status: int):
        self.__data.status = pipeline_status
        task.pipeline_status = pipeline_status
        self.__update_db_task(task)

    def __process_task_info(self, task: VptTasks):
        # module status
        self.__data.task_id = task.task_id
        self.__data.url = task.task_url
        # download video configuration
        self.__data.is_remote_video = False
        if task.task_url:
            self.__data.is_remote_video = True
        if self.__data.is_remote_video:
            self.__data.video_bean.task_url = task.task_url
        else:
            self.__data.video_bean.task_original_video_path = task.task_original_video_path
            self.__data.video_bean.task_upload_video_path = task.task_upload_video_path
        # asr configuration
        self.__data.is_asr = task.is_from_asr_or_subtitle == 1
        if self.__data.is_asr:
            self.__data.asr_bean.audio_rewrite_type = task.audio_rewrite_type
            self.__data.asr_bean.task_url = task.task_url
            self.__data.asr_bean.lang = task.subtitle_lang
        # llm configuration
        self.__data.is_llm = task.is_llm == 1
        if self.__data.is_llm:
            self.__data.llm_bean.llm_text = task.llm_prompt
        # tts configuration
        self.__data.is_tts = task.is_rewrite_to_tts == 1
        if self.__data.is_tts:
            self.__data.tts_bean.tts_server = task.tts_server
            self.__data.tts_bean.tts_speed = task.tts_speed
            self.__data.tts_bean.tts_voice = task.tts_voice
            self.__data.tts_bean.tts_volume = task.tts_volume
        # rewrite subtitle configuration
        self.__data.is_rewrite_subtitle = task.is_rewrite_to_subtitle == 1
        if self.__data.is_rewrite_subtitle:
            resource_font_path = Path(get_resource_font_path())
            subtitle_font_path = resource_font_path / task.subtitle_font
            self.__data.subtitle_bean.subtitle_font = str(subtitle_font_path)
            self.__data.subtitle_bean.subtitle_lang = task.subtitle_lang
            self.__data.subtitle_bean.subtitle_border_color = task.subtitle_border_color
            self.__data.subtitle_bean.subtitle_font_color = task.subtitle_font_color
            self.__data.subtitle_bean.subtitle_position = task.subtitle_position
            self.__data.subtitle_bean.subtitle_size = task.subtitle_size
        # bgm configuration
        self.__data.is_bgm = task.is_bgm == 1
        if self.__data.is_bgm:
            self.__data.bgm_bean.bgm_volume = task.bgm_volume
            self.__data.bgm_bean.uploaded_bgm = task.uploaded_bgm
        # video material configuration
        self.__data.is_material = task.is_video_material == 1
        if self.__data.is_material:
            self.__data.material_video_bean.video_material_type = task.video_material_type
            self.__data.material_video_bean.uploaded_video_material = task.uploaded_video_material
            self.__data.material_video_bean.video_material_splicing_mode = task.video_material_splicing_mode
            self.__data.material_video_bean.video_material_transition_mode = task.video_material_transition_mode
            self.__data.material_video_bean.video_material_video_ratio = task.video_material_video_ratio
            self.__data.material_video_bean.video_material_max_duration = task.video_material_max_duration
            self.__data.material_video_bean.video_material_generate_count = task.video_material_generate_count
            self.__data.material_video_bean.video_material_keyword = task.video_material_keyword

    def __process_asr_info(self, audio_rewrite_type: int, task: VptTasks, asr_config: VptAsrConfig) -> dict:
        args = None
        if audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_LOCAL_WHISPER:
            # 本地部署 本机 whisper
            args = {
                "local_whisper_type": asr_config.local_whisper_type,
                "language": "en"
            }
        elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_REMOTE_WHISPER:
            # 本地部署 远程 whisper
            args = {
                "remote_whisper_type": asr_config.remote_whisper_type,
                "language": "en"
            }
            if asr_config.remote_whisper_type == const.TASK_CONFIG_REMOTE_VLLM_WHISPER:
                # vllm 部署方式
                args.update({
                    "remote_server_url": asr_config.remote_vllm_url,
                    "remote_server_model": asr_config.remote_vllm_model
                })
            elif asr_config.remote_whisper_type == const.TASK_CONFIG_REMOTE_WHISPER_CPP:
                # whisper 部署方式
                args.update({
                    "remote_server_url": asr_config.remote_whisper_cpp_url
                })
        elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_TENCENT_CLOUD:
            # 腾讯云
            args = {
                "secret_id": asr_config.tencent_cloud_secret_id,
                "secret_key": asr_config.tencent_cloud_secret_key,
                "app_id": ""
            }
        elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_XF_YUN:
            # 科大讯飞
            args = {
                "app_id": asr_config.xfyun_appid,
                "api_secret": asr_config.xfyun_secret_key,
                "web_api": asr_config.xfyun_web_api,
            }
        elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_OPENAI:
            # OpenAI
            args = {
                "api_key": asr_config.openai_api_key,
                "model": asr_config.openai_model,
                "base_url": asr_config.openai_base_url
            }
        elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_AZURE:
            # Azure
            args = {
                "subscription_key": asr_config.azure_subscription_key,
                "region": asr_config.azure_region
            }
        elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_BYTEDANCE:
            # 字节-火山引擎
            args = {
                "app_id": asr_config.volcengine_appid,
                "access_token": asr_config.volcengine_access_token,
                "audio_format": "mp3"
            }
        return args

    def __get_subtitle_path(self):
        if self.__data.is_llm:
            return self.__data.llm_bean.llm_full_path
        else:
            return self.__data.asr_bean.subtitle_full_path

    @staticmethod
    def __get_tts_config(tts_server: int):
        tts_config_db = database.get_sync_session()
        tts_config_result = tts_config_db.execute(select(VptTtsConfig).where(VptTtsConfig.tts_server == tts_server))
        tts_config_item = tts_config_result.scalar_one_or_none()
        return tts_config_item

    def process_now(self, task: VptTasks):
        # todo 这个函数太长了，后续需要拆分优化一下
        self.__process_task_info(task)
        # set status to start
        self.__update_pipeline_status(task, const.PIPELINE_STATUS_START)
        # check video
        if self.__data.is_remote_video:
            try:
                self.__update_pipeline_status(task, const.PIPELINE_STATUS_CHECK_VIDEO)
                res = check_video(url=self.__data.video_bean.task_url,
                                  proxy_url=self.__proxy)
            except VPTException as ex:
                logger.exception(f"{task.task_url} check video error")
                task.task_status = ex.code
                task.task_message = ex.message
                self.__update_db_task(task)
                return None
            if not res:
                task.task_status = const.PIPELINE_ERR_UNKNOWN
                task.task_message = f"check video return false, the url: {self.__data.video_bean.task_url} is not allowed"
                self.__update_db_task(task)
                return None
        # download video
        self.__data.status = const.PIPELINE_STATUS_DOWNLOADER
        if self.__data.is_remote_video:
            try:
                res = download_video(
                    url=(self.__data.video_bean if self.__data.video_bean else VideoDownloaderBean()).task_url,
                    task_id=self.__data.task_id,
                    ctx=self.inner_downloader_context,
                    proxy_url=self.__proxy)
            except VPTException as ex:
                logger.exception(f"{task.task_url} download error")
                task.task_status = ex.code
                task.task_message = ex.message
                self.__update_db_task(task)
                return None
            if not res:
                msg = f"{self.__data.video_bean.task_url} download error and return nothing"
                logger.error(msg)
                task.task_status = const.PIPELINE_ERR_UNKNOWN
                task.task_message = msg
                return None
            if res['status'] != 0:
                msg = f"{self.__data.video_bean.task_url} download error, message:{res.get('message', 'unknown message')}"
                logger.error(msg)
                task.task_status = const.PIPELINE_ERR_UNKNOWN
                task.task_message = msg
                return None
            local_video_path = res.get('video_path') or ''
            if not local_video_path:
                msg = f"BaseDownloader download error: local video path is empty"
                logger.error(msg)
                task.task_status = const.PIPELINE_ERR_DOWNLOADER_SAVE_LOCAL_PATH
                task.task_message = msg
                return None
            # 按照以下规则进行路径过滤
            # 源路径：/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/downloads/20260913190132110313.mp4
            # 过滤后的相对路径：storage/downloads/20260913190132110313.mp4
            self.__data.video_bean.video_full_path = local_video_path
            self.__data.video_bean.title = res.get('title') or ''
            self.__data.video_bean.duration = int(res.get('duration') or 0)
            self.__data.video_bean.width = int(res.get('width') or 0)
            self.__data.video_bean.height = int(res.get('height') or 0)
            self.__data.video_bean.metadata = res.get('metadata') or {}
        else:
            # 对于本地上传的视频，只需要获取相应的视频基本信息即可，包括：时长、宽高等等
            real_path = Path(get_current_path()).joinpath(task.task_upload_video_path).expanduser().resolve()
            if not real_path.is_file():
                logger.error(f"upload video is not exists, path: {task.task_upload_video_path}")
                return None
            self.__data.video_bean.width, self.__data.video_bean.height = get_video_width_height(str(real_path))
            self.__data.video_bean.duration = get_video_or_audio_duration(str(real_path))
            self.__data.video_bean.video_full_path = str(real_path)
        # asr or subtitle download
        if self.__data.is_asr:
            try:
                audio_rewrite_type = task.audio_rewrite_type
                # 从 vpt_asr_config 表中获取相应的配置信息
                asr_config = PipelineManager.__get_asr_config()
                args = {}
                if audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_SUBTITLE:
                    if not self.__data.is_remote_video:
                        logger.error(
                            f"local video can't convert subtitle, only remote video can use yt-dlp to download subtitle!")
                        return None
                    res = subtitle_convert(
                        self.__data.asr_bean.task_url,
                        self.__data.asr_bean.lang,
                        task.task_id,
                        proxy_url=self.__proxy
                    )
                else:
                    args = self.__process_asr_info(audio_rewrite_type, task, asr_config)
                    res = asr_convert(
                        self.__data.video_bean.video_full_path,
                        audio_rewrite_type=audio_rewrite_type,
                        proxy_url=self.__proxy,
                        **args
                    )
                if not res:
                    logger.error(f"asr unknown, can't get result")
                    return None
                self.__data.asr_bean.audio_rewrite_type = audio_rewrite_type
                self.__data.asr_bean.subtitle_full_path = res
            except VPTException as ex:
                logger.exception(f"{task.task_url} download error")
                task.task_status = ex.code
                task.task_message = ex.message
                self.__update_db_task(task)
                return None
        # llm prompt rewrite
        if self.__data.is_llm:
            if not self.__data.is_asr:
                # 如果没有进行ASR处理，只有视频，那么是无法进行LLM处理的
                logger.error(f"LLM rewrite need ASR result")
                return None
        try:
            srt_path = Path(self.__data.asr_bean.subtitle_full_path).expanduser().resolve()
            llm_rewrite_dir = asyncio.run(get_llm_rewrite_path())
            if not llm_rewrite_dir:
                logger.error(f"llm rewrite dir is not exists")
                return None
            llm_rewrite_path = Path(llm_rewrite_dir).joinpath(srt_path.name)
            llm_config_item = PipelineManager.__get_llm_config()
            api_key = llm_config_item.api_key
            base_url = llm_config_item.base_url
            model = llm_config_item.llm_model_name
            llm_rewrite(
                prompt=self.__data.llm_bean.llm_text,
                src_path=str(srt_path),
                dst_path=str(llm_rewrite_path),
                api_key=api_key,
                base_url=base_url,
                model=model
            )
            if not llm_rewrite_path.is_file():
                msg = f"{task.task_url} llm rewrite error, llm rewrite path is None"
                logger.exception(msg)
                task.task_status = const.PIPELINE_ERR_FILE_SAVE
                task.task_message = msg
                self.__update_db_task(task)
                return None
            self.__data.llm_bean.llm_full_path = str(llm_rewrite_path)
        except VPTException as ex:
            logger.exception(f"{task.task_url} llm rewrite error")
            task.task_status = ex.code
            task.task_message = ex.message
            self.__update_db_task(task)
            return None
        # rewrite to tts
        if self.__data.is_tts:
            tts_rewrite_dir = asyncio.run(get_tts_rewrite_path())
            if not tts_rewrite_dir:
                msg = f"config.yaml storage.tts_rewrite not set!"
                logger.error(msg)
                task.task_status = const.PIPELINE_ERR_FILE_NOT_FOUND
                task.task_message = msg
                self.__update_db_task(task)
                return None
            subtitle_path = self.__get_subtitle_path()
            if not subtitle_path:
                msg = f"Using the TTS module required by the ASR module."
                logger.error(msg)
                task.task_status = const.PIPELINE_ERR_FILE_NOT_FOUND
                task.task_message = msg
                self.__update_db_task(task)
                return None
            tts_server = const.TTS_LIST_AZURE_TTS_V1
            if self.__data.tts_bean.tts_server == const.TTS_LIST_AZURE_TTS_V1_VAL:
                tts_server = const.TTS_LIST_AZURE_TTS_V1
            elif self.__data.tts_bean.tts_server == const.TTS_LIST_AZURE_TTS_V2_VAL:
                tts_server = const.TTS_LIST_AZURE_TTS_V2
            elif self.__data.tts_bean.tts_server == const.TTS_LIST_SILICON_FLOW_TTS_VAL:
                tts_server = const.TTS_LIST_SILICON_FLOW_TTS
            elif self.__data.tts_bean.tts_server == const.TTS_LIST_GOOGLE_GEMINI_TTS_VAL:
                tts_server = const.TTS_LIST_GOOGLE_GEMINI_TTS
            tts_config_item = PipelineManager.__get_tts_config(tts_server)
            if not tts_config_item:
                msg = f"tts config is not exists"
                logger.error(msg)
                task.task_status = const.PIPELINE_ERR_TTS_CONFIG_DB
                task.task_message = msg
                self.__update_db_task(task)
                return None
            res = tts_from_subtitle(
                tts_engine=self.__data.tts_bean.tts_server,
                subtitle_path=subtitle_path,
                voice=self.__data.tts_bean.tts_voice,
                lang=get_lang_from_voice(self.__data.tts_bean.tts_voice),
                api_key=tts_config_item.tts_apikey,
                region=tts_config_item.tts_area,
                proxy_url=self.__proxy
            )
            if not res:
                msg = f"tts return empty!"
                logger.error(msg)
                task.task_status = const.PIPELINE_ERR_TTS_RETURN
                task.task_message = msg
                self.__update_db_task(task)
                return None
            res_path = Path(res).expanduser().resolve()
            if not res_path.is_file():
                msg = f"tts return path: {res_path} not exists!"
                logger.error(msg)
                task.task_status = const.PIPELINE_ERR_FILE_NOT_FOUND
                task.task_message = msg
                self.__update_db_task(task)
                return None
            self.__data.tts_bean.tts_full_path = str(res_path)
        # material video
        if self.__data.is_material:
            subtitle_path = self.__get_subtitle_path()
            res_list = video_overlay(
                video_file_path=self.__data.video_bean.video_full_path,
                subtitle_file_path=subtitle_path,
                material_type=self.__data.material_video_bean.video_material_type,
                material_keyword=self.__data.material_video_bean.video_material_keyword,
                material_video_ratio=self.__data.material_video_bean.video_material_video_ratio,
                material_max_duration=self.__data.material_video_bean.video_material_max_duration,
                proxy_url=self.__proxy
            )
            self.__data.material_video_bean.video_materials = res_list
        # assembly video(ffmpeg)
        print(self.__data)


pipeline = PipelineManager()

if __name__ == "__main__":
    init_config()
    init_downloader()
    task_id = "20260913190132110313"
    database.start()
    db = database.get_sync_session()
    result = db.execute(select(VptTasks).where(
        VptTasks.task_id == task_id,
        VptTasks.is_deleted == 0
    ).order_by(VptTasks.create_time.asc()).limit(1))
    item = result.scalar_one_or_none()
    if item:
        pipeline.process_now(item)
