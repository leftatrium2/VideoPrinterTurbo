import logging

logging.getLogger('apscheduler').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def my_listener(event):
    if event.exception:
        logger.error(f"job_id: {event.job_id}")
        logger.exception(event.exception)
