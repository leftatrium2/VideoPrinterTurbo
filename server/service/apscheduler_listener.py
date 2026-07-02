import logging

logging.getLogger('apscheduler').setLevel(logging.WARNING)


def my_listener(event):
    if event.exception:
        logging.error(f"job_id: {event.job_id}")
        logging.exception(event.exception)
