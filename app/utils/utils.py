"""Utility functions — path resolution, UUID, JSON, SRT formatting, etc."""

import json
import locale
import os
import threading
from pathlib import Path
from typing import Any
from uuid import uuid4

from loguru import logger

from app.models import const


def get_response(status: int, data: Any = None, message: str = ""):
    obj = {"status": status}
    if data is not None:
        obj["data"] = data
    if message:
        obj["message"] = message
    return obj


def to_json(obj):
    try:
        def serialize(o):
            if isinstance(o, (int, float, bool, str)) or o is None:
                return o
            elif isinstance(o, bytes):
                return "*** binary data ***"
            elif isinstance(o, dict):
                return {k: serialize(v) for k, v in o.items()}
            elif isinstance(o, (list, tuple)):
                return [serialize(item) for item in o]
            elif hasattr(o, "__dict__"):
                return serialize(o.__dict__)
            else:
                return None

        serialized_obj = serialize(obj)
        return json.dumps(serialized_obj, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"failed to serialize object to json: {str(e)}")
        return None


def get_uuid(remove_hyphen: bool = False):
    u = str(uuid4())
    return u.replace("-", "") if remove_hyphen else u


def root_dir():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


def storage_dir(sub_dir: str = "", create: bool = False):
    d = os.path.join(root_dir(), "storage")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if create and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    return d


def resource_dir(sub_dir: str = ""):
    d = os.path.join(root_dir(), "resource")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    return d


def task_dir(sub_dir: str = ""):
    d = os.path.join(storage_dir(), "tasks")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    return d


def font_dir(sub_dir: str = ""):
    d = resource_dir("fonts")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    return d


def song_dir(sub_dir: str = ""):
    d = resource_dir("songs")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    return d


def public_dir(sub_dir: str = ""):
    d = resource_dir("public")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    return d


def downloads_dir():
    """Directory for yt-dlp downloaded videos."""
    from app.config import config
    d = config.app.downloads_dir or os.path.join(root_dir(), "downloads")
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    return d


def run_in_background(func, *args, **kwargs):
    def run():
        try:
            func(*args, **kwargs)
        except Exception as e:
            logger.error(f"run_in_background error: {e}", exc_info=True)

    thread = threading.Thread(target=run, daemon=False)
    thread.start()
    return thread


def time_convert_seconds_to_hmsm(seconds) -> str:
    hours = int(seconds // 3600)
    seconds = seconds % 3600
    minutes = int(seconds // 60)
    milliseconds = int(seconds * 1000) % 1000
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def text_to_srt(idx: int, msg: str, start_time: float, end_time: float) -> str:
    start = time_convert_seconds_to_hmsm(start_time)
    end = time_convert_seconds_to_hmsm(end_time)
    return f"{idx}\n{start} --> {end}\n{msg}\n"


def str_contains_punctuation(word):
    for p in const.PUNCTUATIONS:
        if p in word:
            return True
    return False


def split_string_by_punctuations(s):
    result = []
    txt = ""
    for i in range(len(s)):
        char = s[i]
        if char == "\n":
            result.append(txt.strip())
            txt = ""
            continue
        previous_char = s[i - 1] if i > 0 else ""
        next_char = s[i + 1] if i < len(s) - 1 else ""

        if char == "." and previous_char.isdigit() and next_char.isdigit():
            txt += char
            continue
        if char == "," and previous_char.isdigit() and next_char.isdigit():
            txt += char
            continue
        if char not in const.PUNCTUATIONS:
            txt += char
        else:
            result.append(txt.strip())
            txt = ""
    result.append(txt.strip())
    return list(filter(None, result))


def md5(text):
    import hashlib
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def get_system_locale():
    try:
        loc = locale.getdefaultlocale()
        return loc[0].split("_")[0] if loc[0] else "en"
    except Exception:
        return "en"


def load_locales(i18n_dir):
    _locales = {}
    for root, dirs, files in os.walk(i18n_dir):
        for file in files:
            if file.endswith(".json"):
                lang = file.split(".")[0]
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    _locales[lang] = json.loads(f.read())
    return _locales


def parse_extension(filename):
    return Path(filename).suffix.lower().lstrip(".")
