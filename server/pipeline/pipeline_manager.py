import logging
from typing import Optional

from sqlalchemy import select

from config.config import init_config
from models.model import VptTasks
from pipeline.bean.pipeline_data import PipeLineData
from pipeline.bean.video_bean import VideoBean
from pipeline.downloader.base import DownloaderContext
from pipeline.utils.pipeline_asr_utls import asr_convert
from pipeline.utils.pipeline_llm_utils import llm_rewrite
from pipeline.utils.pipeline_video_downloader_utils import check_video, download_video, init_downloader
from utils import const
from utils.database import database
from utils.exception import VPTException

logger = logging.getLogger(__name__)


class PipelineManager:

    def __init__(self):
        self.__proxy = None
        self.__data: PipeLineData = PipeLineData()
        self.inner_downloader_context = PipelineManager.InnerDownloaderContext()

    class InnerDownloaderContext(DownloaderContext):

        def on_create(self, url: str):
            logger.info(f"on_create: url: {url}")
            pass

        def on_start(self, url: str):
            pass

        def on_progress(self, url: str, codec_type: int, progress: float):
            pass

        def on_complete(self, url: str):
            pass

        def on_error(self, url: str, error: Exception):
            pass

    def set_proxy(self, proxy: str):
        self.__proxy = proxy

    def get_data(self) -> Optional[PipeLineData]:
        return self.__data

    def init(self):
        self.__data = PipeLineData()

    def __update_db_task(self, task: VptTasks):
        db = database.get_sync_session()
        result = db.execute(select(VptTasks).where(
            VptTasks.task_id == task.task_id,
            VptTasks.is_deleted == 0
        ))
        item = result.scalar_one_or_none()
        if not item:
            logger.error(f"task not found: {task.task_id}")
            return
        db.commit()
        db.refresh()

    def __update_pipeline_status(self, task: VptTasks, pipeline_status: int):
        self.__data.status = pipeline_status
        task.pipeline_status = pipeline_status
        self.__update_db_task(task)

    def process_now(self, task: VptTasks):
        # module status
        is_asr = task.is_from_asr_or_subtitle
        is_llm = task.is_llm
        is_tts = task.is_rewrite_to_tts
        is_subtitle = task.is_rewrite_to_subtitle
        is_bgm = task.is_bgm
        is_material = task.is_video_material
        self.__update_pipeline_status(task, const.PIPELINE_STATUS_START)
        # check video
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
            task.task_message = "check video return false,but cant get error message"
            self.__update_db_task(task)
            return None
        # download video
        self.__data.status = const.PIPELINE_STATUS_DOWNLOADER
        self.__data.video_bean = VideoBean()
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
        self.__data.video_bean.url = res.get('url') or ''
        self.__data.video_bean.video_path = res.get('video_path') or ''
        self.__data.video_bean.title = res.get('title') or ''
        self.__data.video_bean.duration = int(res.get('duration') or 0)
        self.__data.video_bean.width = int(res.get('width') or 0)
        self.__data.video_bean.height = int(res.get('height') or 0)
        self.__data.video_bean.metadata = res.get('metadata') or {}
        # asr or subtitle download
        if is_asr:
            try:
                res = asr_convert(
                    self.__data.video_bean.video_path
                )
            except VPTException as ex:
                logger.error(f"{task.task_url} download error, message:{ex}")
                task.task_status = ex.code
                task.task_message = ex.message
                self.__update_db_task(task)
                return None
        # llm prompt rewrite
        if is_llm:
            if not is_asr:
                # 如果没有进行ASR处理，只有视频，那么是无法进行LLM处理的
                logger.error(f"LLM rewrite need ASR result")
                return None
            try:
                llm_rewrite(
                    prompt="翻译为中文",
                    src_path="",
                    dst_path="",
                    api_key="sk-ab80cf21b3884471aa20ce8613fcbd7b",
                    base_url="https://api.deepseek.com",
                    model="deepseek-flash"
                )
            except VPTException as ex:
                logger.error(f"{task.task_url} llm rewrite error, message:{ex}")
                task.task_status = ex.code
                task.task_message = ex.message
                self.__update_db_task(task)
                return None
        # rewrite to tts
        # rewrite to subtitle
        # bgm


pipeline = PipelineManager()

if __name__ == "__main__":
    class TestDownloaderContext(DownloaderContext):
        def on_create(self, url: str):
            print(f"on_create: {url}")

        def on_start(self, url: str):
            print(f"on_start: {url}")

        def on_progress(self, url: str, codec_type: int, progress: float):
            print(f"on_progress: codec={codec_type}, progress={progress:.1%}")

        def on_error(self, url: str, error: Exception):
            print(f"on_error: {url}: {error}")

        def on_complete(self, url: str):
            print(f"on_complete: {url}")


    init_config()
    init_downloader()
    task_id = "20260727215533153521"
    database.start()
    db = database.get_sync_session()
    result = db.execute(select(VptTasks).where(
        VptTasks.task_id == task_id,
        VptTasks.is_deleted == 0
    ).order_by(VptTasks.create_time.asc()).limit(1))
    item = result.scalar_one_or_none()
    if item:
        url = "https://www.youtube.com/watch?v=IlbPO9Vmuuo"
        result = check_video(url, None)
        if not result:
            logger.error(f"task check failed: {task_id}")
        result = download_video(url=url, task_id=task_id, ctx=TestDownloaderContext(),
                                proxy_url="http://127.0.0.1:7890")
        print(result)
    # if item:
    #     result = pipeline.video_overlay(
    #         "/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/downloads/Give Me 9 Minutes, I'll Make You AI-Native.mp4",
    #         "/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/video_to_text/Give Me 9 Minutes, I'll Make You AI-Native.srt",
    #         material_type=item.video_material_type,
    #         material_keyword=item.video_material_keyword,
    #         material_video_ratio=item.video_material_video_ratio,
    #         material_max_duration=item.video_material_max_duration
    #     )
    #     if not result:
    #         print("video_overlay return False")
    #     curr_data = pipeline.get_data()
    #     print(curr_data)
