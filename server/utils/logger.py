import logging

logging.basicConfig(level=logging.INFO,  # 日志级别：DEBUG/INFO/WARNING/ERROR/CRITICAL
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                    )
# 2. 获取日志实例
logger = logging.getLogger(__name__)
