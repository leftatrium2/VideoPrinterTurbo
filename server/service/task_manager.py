from sqlalchemy import select, and_
from tenacity import sleep

from config.config import init_config
from models.model import VptTasks
from pipeline.pipeline_manager import pipeline, init_downloader
from utils import const
from utils.database import database
from utils.logger import logger


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
                    select(VptTasks).where(and_(
                        VptTasks.pipeline_status == const.PIPELINE_STATUS_INI,
                        VptTasks.is_deleted == 0
                    )).order_by(VptTasks.create_time.asc()).limit(1)
                )
                task = result.scalar_one_or_none()
                if not task:
                    sleep(5)
                    continue
                pipeline.init()
                pipeline.process_now(task)
                print(f"task success: {task.id}")
            except Exception as e:
                logger.exception(f"job failed: {e}")
        pass

    async def start(self):
        logger.info("Starting TaskManager")
        # self.processes_threading = threading.Thread(target=self.process, daemon=True)
        # self.processes_threading.start()

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
