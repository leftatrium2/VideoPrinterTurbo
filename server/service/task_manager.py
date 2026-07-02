from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.model import VptTask
from server.utils.logger import logger
from service import task_const
from service.apscheduler_listener import my_listener
from utils import const

g_executors = {
    'default': ThreadPoolExecutor(task_const.TASKMANAGER_MAX_THREADS)
}
g_job_defaults = {
    'coalesce': True,
    'max_instances': 1
}
g_schedule = BackgroundScheduler(job_defaults=g_job_defaults, executors=g_executors)


class TaskManager(object):
    def __init__(self):
        pass

    def _get_task(self):
        pass

    async def start(self):
        logger.info("Starting TaskManager")
        g_schedule.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        if not g_schedule.running:
            g_schedule.start()

    async def stop(self):
        logger.info("Stopping TaskManager")
        if g_schedule.running:
            g_schedule.shutdown()


task_manager = TaskManager()
