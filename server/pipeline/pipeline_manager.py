import logging
from typing import Optional

from sqlalchemy import select

from config.config import init_config
from models.model import VptTasks
from pipeline.bean.pipeline_data import PipeLineData
from pipeline.bean.video_bean import VideoBean
from pipeline.downloader.base import DownloaderContext
from pipeline.utils.pipeline_video_downloader_utils import check_video, download_video, init_downloader
from service import task_const
from utils.database import database


class PipelineManager:

    def __init__(self):
        self.__proxy = None
        self._data: PipeLineData = PipeLineData()
        self.inner_downloader_context = PipelineManager.InnerDownloaderContext()

    class InnerDownloaderContext(DownloaderContext):

        def on_create(self, url: str):
            logging.info(f"on_create: url: {url}")
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
        return self._data

    def init(self):
        self._data = PipeLineData()

    def process_now(self, task: VptTasks) -> int:
        res = check_video(url=task.task_url,
                          proxy_url=self.__proxy)
        if not res:
            return task_const.TASK_STATUS_ERROR_DOWNLOAD_CHECK
        # download video
        self._data.video_bean = VideoBean()
        res = download_video(url=task.task_url,
                             task_id=task.task_id,
                             ctx=self.inner_downloader_context,
                             proxy_url=self.__proxy)
        if not res or res['status'] != 0:
            logging.error(f"{task.task_url} download error, message:{res['message']}")
            return task_const.TASK_STATUS_ERROR_DOWNLOAD
        self._data.video_bean.url = res['url'] or ""
        self._data.video_bean.video_path = res['video_path'] or ""
        self._data.video_bean.title = res['title'] or ""
        self._data.video_bean.duration = int(res['duration'] or 0)
        self._data.video_bean.width = int(res['width'] or 0)
        self._data.video_bean.height = int(res['height'] or 0)
        self._data.video_bean.metadata = res['metadata'] or {}
        # asr or subtitle download
        if task.is_from_asr_or_subtitle:
            pass
        # llm prompt rewrite
        if task.is_llm:
            pass
        # rewrite to tts
        # rewrite to subtitle
        # bgm

        return task_const.TASK_STATUS_SUCCESS


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
            logging.error(f"task check failed: {task_id}")
        result = pipeline.download(url=url, task_id=task_id, ctx=TestDownloaderContext(), is_download_proxy=True)
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
