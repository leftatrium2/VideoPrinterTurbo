import logging
from pathlib import Path
from typing import Optional

from sqlalchemy import select

from config.config import init_config
from models.model import VptTasks, VptAsrConfig
from pipeline.bean.pipeline_data import PipeLineData
from pipeline.bean.video_downloader_bean import VideoDownloaderBean
from pipeline.downloader.base import DownloaderContext
from pipeline.utils.pipeline_asr_utls import asr_convert
from pipeline.utils.pipeline_video_downloader_utils import check_video, download_video, init_downloader
from utils.video_utils import get_video_width_height, get_video_or_audio_duration
from utils import const
from utils.database import database
from utils.exception import VPTException
from utils.file_utils import get_current_path

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
        db = database.get_sync_session()
        result = db.execute(select(VptAsrConfig).limit(1))
        item = result.scalar_one_or_none()
        if not item:
            raise VPTException(const.PIPELINE_ERR_ASR_NOT_CONFIGURATION, "asr config not found")
        return item

    def __update_pipeline_status(self, task: VptTasks, pipeline_status: int):
        self.__data.status = pipeline_status
        task.pipeline_status = pipeline_status
        self.__update_db_task(task)

    def process_now(self, task: VptTasks):
        # module status
        is_need_download_video = False
        if task.task_url:
            is_need_download_video = True
        is_asr = task.is_from_asr_or_subtitle == 1
        is_llm = task.is_llm == 1
        is_tts = task.is_rewrite_to_tts == 1
        is_subtitle = task.is_rewrite_to_subtitle == 1
        is_bgm = task.is_bgm == 1
        is_material = task.is_video_material == 1
        self.__update_pipeline_status(task, const.PIPELINE_STATUS_START)
        # check video
        if is_need_download_video:
            try:
                self.__update_pipeline_status(task, const.PIPELINE_STATUS_CHECK_VIDEO)
                res = check_video(url=task.task_url,
                                  proxy_url=self.__proxy)
            except VPTException as ex:
                task.task_status = ex.code
                task.task_message = ex.message
                self.__update_db_task(task)
                return None
            if not res:
                task.task_status = const.TASK_ERR_UNKNOWN
                task.task_message = f"check video return false, the url: {task.task_url} is not allowed"
                self.__update_db_task(task)
                return None
        # download video
        self.__data.status = const.PIPELINE_STATUS_DOWNLOADER
        self.__data.video_bean = VideoDownloaderBean()
        self.__data.video_bean.task_url = task.task_url
        self.__data.video_bean.task_original_video_path = task.task_original_video_path
        self.__data.video_bean.task_upload_video_path = task.task_upload_video_path
        if is_need_download_video:
            try:
                res = download_video(url=task.task_url,
                                     task_id=task.task_id,
                                     ctx=self.inner_downloader_context,
                                     proxy_url=self.__proxy)
            except VPTException as ex:
                msg = f"{task.task_url} download error, message:{ex}"
                logger.error(msg)
                task.task_status = ex.code
                task.task_message = ex.message
                self.__update_db_task(task)
                return None
            if not res:
                msg = f"{task.task_url} download error and return nothing"
                logger.error(msg)
                task.task_status = const.TASK_ERR_UNKNOWN
                task.task_message = msg
                return None
            if res['status'] != 0:
                msg = f"{task.task_url} download error, message:{res.get('message', 'unknown message')}"
                logger.error(msg)
                task.task_status = const.TASK_ERR_UNKNOWN
                task.task_message = msg
                return None
            self.__data.video_bean.video_path = res.get('video_path') or ''
            self.__data.video_bean.title = res.get('title') or ''
            self.__data.video_bean.duration = int(res.get('duration') or 0)
            self.__data.video_bean.width = int(res.get('width') or 0)
            self.__data.video_bean.height = int(res.get('height') or 0)
            self.__data.video_bean.metadata = res.get('metadata') or {}
        else:
            # 对于本地上传的视频，只需要获取相应的视频基本信息即可，包括：时长、宽高等等
            self.__data.video_bean.video_path = task.task_upload_video_path
            real_path = Path(get_current_path()).joinpath(task.task_upload_video_path).expanduser().resolve()
            if not real_path.is_file():
                raise VPTException(const.PIPELINE_ERR_FILE_NOT_FOUND,
                                   f"upload video is not exists, path: {task.task_upload_video_path}")
            self.__data.video_bean.width, self.__data.video_bean.height = get_video_width_height(str(real_path))
            self.__data.video_bean.duration = get_video_or_audio_duration(str(real_path))
        exit(0)
        # asr or subtitle download
        if is_asr:
            try:
                audio_rewrite_type = task.audio_rewrite_type
                # 从 vpt_asr_config 表中获取相应的配置信息
                asr_config = PipelineManager.__get_asr_config()
                args = {}
                if audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_LOCAL_WHISPER:
                    # 本地部署 本机 whisper
                    args = {
                        "local_whisper_type": asr_config.local_whisper_type
                    }
                elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_REMOTE_WHISPER:
                    # 本地部署 远程 whisper
                    args = {
                        "remote_whisper_type": asr_config.remote_whisper_type,
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
                    pass
                elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_XF_YUN:
                    # 科大讯飞
                    args = {
                        "app_id": asr_config.xfyun_appid,
                        "api_secret": asr_config.xfyun_secret_key,
                        "web_api": asr_config.xfyun_web_api,
                    }
                    pass
                elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_OPENAI:
                    # OpenAI
                    args = {
                        "api_key": asr_config.openai_api_key,
                        "model": asr_config.openai_model,
                        "base_url": asr_config.openai_base_url
                    }
                    pass
                elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_AZURE:
                    # Azure
                    args = {
                        "subscription_key": asr_config.azure_subscription_key,
                        "region": asr_config.azure_region
                    }
                    pass
                elif audio_rewrite_type == const.TASK_CONFIG_ASR_FROM_BYTEDANCE:
                    # 字节-火山引擎
                    args = {
                        "app_id": asr_config.volcengine_appid,
                        "access_token": asr_config.volcengine_access_token,
                        "audio_format": "mp3"
                    }
                    pass
                res = asr_convert(
                    self.__data.video_bean.video_path,
                    audio_rewrite_type=audio_rewrite_type,
                    **args
                )
                if not res:
                    raise VPTException(const.PIPELINE_ERR_ASR_UNKNOWN, "asr unknown, can't get result")
                self.__data.asr_bean.audio_rewrite_type = audio_rewrite_type
                self.__data.asr_bean.subtitle_path = res
            except VPTException as ex:
                logger.error(f"{task.task_url} download error, message:{ex}")
                task.task_status = ex.code
                task.task_message = ex.message
                self.__update_db_task(task)
                return None
        # llm prompt rewrite
        # if is_llm:
        #     if not is_asr:
        #         # 如果没有进行ASR处理，只有视频，那么是无法进行LLM处理的
        #         logger.error(f"LLM rewrite need ASR result")
        #         return None
            # try:
            #     llm_rewrite(
            #         prompt="翻译为中文",
            #         src_path="",
            #         dst_path="",
            #         api_key="sk-ab80cf21b3884471aa20ce8613fcbd7b",
            #         base_url="https://api.deepseek.com",
            #         model="deepseek-flash"
            #     )
            # except VPTException as ex:
            #     logger.error(f"{task.task_url} llm rewrite error, message:{ex}")
            #     task.task_status = ex.code
            #     task.task_message = ex.message
            #     self.__update_db_task(task)
            #     return None
        # rewrite to tts
        # rewrite to subtitle
        # bgm


pipeline = PipelineManager()

if __name__ == "__main__":
    init_config()
    init_downloader()
    task_id = "20260916151852691865"
    database.start()
    db = database.get_sync_session()
    result = db.execute(select(VptTasks).where(
        VptTasks.task_id == task_id,
        VptTasks.is_deleted == 0
    ).order_by(VptTasks.create_time.asc()).limit(1))
    item = result.scalar_one_or_none()
    if item:
        pipeline.process_now(item)
