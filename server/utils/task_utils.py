import datetime
import logging
import random
import uuid

logger = logging.getLogger(__name__)


def gen_task_id() -> str:
    try:
        curr_ts = datetime.datetime.now()
        num = random.randint(100000, 999999)
        curr_date_str = curr_ts.strftime("%Y%m%d%H%M%S") + str(num)
        return curr_date_str
    except Exception as e:
        logger.error(e)
    return str(uuid.uuid4())


if __name__ == "__main__":
    print(gen_task_id())
