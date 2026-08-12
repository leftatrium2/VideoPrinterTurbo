import logging
import os.path

from moviepy import VideoFileClip


def get_video_duration(file_path: str) -> int:
    if not os.path.exists(file_path):
        return 0
    try:
        with VideoFileClip(file_path) as clip:
            return int(clip.duration)
    except Exception as exc:
        logging.error(exc)
        return 0
