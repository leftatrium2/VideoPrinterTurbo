import asyncio
import logging
import threading

from sqlalchemy import select, and_
from tenacity import sleep

from config.config import init_config
from models.model import VptTask
from pipeline.downloader.base import PipeLineContext
from pipeline.pipeline_manager import pipeline, init_downloader
from utils.logger import logger
from service import task_const
from utils.database import database


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
        session = database.get_sync_session()
        while True:
            try:
                result = session.execute(
                    select(VptTask).where(and_(
                        VptTask.status == task_const.TASK_STATUS_QUEUE,
                        VptTask.is_deleted == 0
                    )).order_by(VptTask.create_time.asc()).limit(1)
                )
                task = result.scalar_one_or_none()
                if not task:
                    sleep(5)
                    continue
                pipeline.init(task)
                result = pipeline.process_now(task)
                if not result:
                    logger.error(f"task failed: {task.id}")
                    task.status = task_const.TASK_STATUS_ERROR_UNKNOWN
                    continue
                print(f"task success: {task.id}")
                sleep(5)
            except Exception as e:
                logger.exception(f"job failed: {e}")
        pass

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
