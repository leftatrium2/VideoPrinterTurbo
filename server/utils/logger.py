import logging

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                    force=True
                    )
# 2. Get logger instance
logger = logging.getLogger(__name__)
