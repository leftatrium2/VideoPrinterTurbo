import logging

logging.basicConfig(level=logging.INFO,  # Log level: DEBUG/INFO/WARNING/ERROR/CRITICAL
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                    )
# 2. Get logger instance
logger = logging.getLogger(__name__)
