import queue
import threading

from sqlalchemy import select, and_
from tenacity import sleep

from models.model import VptTask
from pipeline.pipeline import pipeline
from server.utils.logger import logger
from service import task_const
from utils.database import database


# 任务管理器
# 第一期，先按照串行处理方式进行，一次只进行一个任务
# 后面需要优化的点：
# 1. 下载实际上是可以并行的
# 2. Fast Whisper 在本机运行的时候，是串行的。但其他的ASR线上服务是可以并行的
# 3. 很多本地运行的大模型，都只能串行，但线上的服务，大部分都可以并行
# 所以，需要有一个专门的设置页面，来设置并行的数量，并在任务并行拥堵的时候，给出拥堵的提示
class TaskManager(object):
    processes_threading = None

    def __init__(self):
        pass

    def __processes_task(self):
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
                pipeline.process(task.task_id)
            except Exception as e:
                logger.exception(f"job failed: {e}")
        pass

    async def start(self):
        logger.info("Starting TaskManager")
        # self.processes_threading = threading.Thread(target=self.__processes_task, daemon=True)
        # self.processes_threading.start()

    async def stop(self):
        logger.info("Stopping TaskManager")
        database.remove_sync_session()
        if database.sync_engine:
            database.sync_engine.dispose()


task_manager = TaskManager()
