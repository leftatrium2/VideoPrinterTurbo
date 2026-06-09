"""Application initialization - logging setup."""
import os
import sys
from loguru import logger


def __init_logger():
    root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    def format_record(record):
        file_path = record["file"].path
        relative_path = os.path.relpath(file_path, root_dir)
        record["file"].path = f"./{relative_path}"
        _format = (
            "<green>{time:%Y-%m-%d %H:%M:%S}</> | "
            + "<level>{level}</> | "
            + '"{file.path}:{line}":<blue> {function}</> '
            + "- <level>{message}</>"
            + "\n"
        )
        return _format

    logger.remove()
    logger.add(
        sys.stdout,
        level="DEBUG",
        format=format_record,
        colorize=True,
    )


__init_logger()
