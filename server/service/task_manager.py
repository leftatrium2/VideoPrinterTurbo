import logging
import threading

from sqlalchemy import select, and_
from tenacity import sleep

from config.config import init_config
from models.model import VptTasks
from pipeline.pipeline_manager import pipeline, init_downloader
from utils import const
from utils.database import database

logger = logging.getLogger(__name__)


# Task Manager
# Phase 1: Process tasks sequentially, one task at a time
# Points for future optimization:
# 1. Downloads can actually be parallelized
# 2. When running Fast Whisper locally, it is serial. But other online ASR services can be parallelized
# 3. Many locally-run large models can only run serially, but most online services can be parallelized
# Therefore, a dedicated settings page is needed to configure the level of parallelism,
# and provide congestion alerts when task processing is overloaded
class TaskManager(object):
    processes_threading = None

    def process(self):
        db = database.get_sync_session()
        try:
            while True:
                try:
                    # 从任务表里面，获取一个任务
                    # 要求：
                    # 1. pipeline_status == const.PIPELINE_STATUS_INIT（状态是INIT）
                    # 2. is_deleted == 0 （未删除）
                    result = db.execute(
                        select(VptTasks).where(and_(
                            VptTasks.pipeline_status == const.PIPELINE_STATUS_INIT,
                            VptTasks.is_deleted == 0
                        )).order_by(VptTasks.create_time.asc()).limit(1)
                    )
                    task = result.scalar_one_or_none()
                    if not task:
                        sleep(5)
                        logger.info("No task to process now")
                        continue
                    logger.info(f"process task: {task.task_id}")
                    pipeline.clear_data()
                    pipeline.process_now(task)
                    logger.info(f"task success: {task.task_id}")
                except Exception as e:
                    logger.exception(f"job failed: {e}")
        finally:
            db.close()

    async def start(self):
        logger.info("Starting TaskManager")
        self.processes_threading = threading.Thread(target=self.process, daemon=True)
        self.processes_threading.start()

    async def stop(self):
        logger.info("Stopping TaskManager")
        database.remove_sync_session()
        if database.sync_engine:
            database.sync_engine.dispose()


task_manager = TaskManager()

if __name__ == "__main__":
    init_config()
    init_downloader()
    database.start()
    task_manager.process()
