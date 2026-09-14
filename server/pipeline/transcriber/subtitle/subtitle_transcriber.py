# 获取给定 url 的字幕文件
import asyncio
import glob
import json
import logging
import os
import shutil
from typing import Optional

import yt_dlp

from config.config import init_config
from utils import const
from utils.convert_subtitle_ttml_to_srt import convert_subtitle_ttml_to_srt
from utils.exception import VPTException
from utils.file_utils import get_subtitle_path

logger = logging.getLogger(__name__)


class SubTitleTranscriber(object):
    _yt_dlp_subtitle = [
        "af",
        "sq",
        "am",
        "ar",
        "hy",
        "az",
        "eu",
        "be",
        "bn",
        "bg",
        "my",
        "zh-Hans",
        "zh-Hant",
        "cs",
        "da",
        "nl",
        "en",
        "en-orig",
        "et",
        "fil",
        "fi",
        "fr",
        "gl",
        "ka",
        "de",
        "el",
        "gu",
        "iw",
        "hi",
        "hu",
        "is",
        "id",
        "it",
        "ja",
        "jv",
        "kn",
        "km",
        "ko",
        "lo",
        "lv",
        "lt",
        "mk",
        "ms",
        "ml",
        "mr",
        "mn",
        "ne",
        "no",
        "fa",
        "pl",
        "pt",
        "pt-PT",
        "pa",
        "ro",
        "ru",
        "si",
        "sk",
        "es",
        "su",
        "sw",
        "sv",
        "ta",
        "te",
        "th",
        "tr",
        "uk",
        "uz",
        "vi",
        "zu"
    ]

    def __init__(self):
        pass

    def subtitle(self, url: str, index: int, proxy_url: Optional[str] = None) -> Optional[str]:
        lang = self._yt_dlp_subtitle[index]
        subtitle_path = asyncio.run(get_subtitle_path())
        if not subtitle_path:
            logger.error("Subtitle path is empty")
            return None
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,  # 没有人工字幕时回退到自动字幕
            'subtitleslangs': [lang],
            'subtitlesformat': 'ttml',
            'outtmpl': '%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }
        if proxy_url:
            # socks5h:// — DNS 交给代理服务器解析，对于翻墙场景更可靠
            if proxy_url.startswith("socks5://"):
                proxy_url = proxy_url.replace("socks5://", "socks5h://", 1)
            ydl_opts['proxy'] = proxy_url
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info['id']
        # yt-dlp 生成的字幕文件命名通常是 {id}.{lang}.{ext}
        pattern = f"{video_id}.{lang}.ttml"
        matches = glob.glob(pattern)
        if not matches:
            raise VPTException(const.PIPELINE_ERR_FILE_NOT_FOUND, f"未找到字幕文件，匹配模式: {pattern}")
        src_path = matches[0]
        ttml_path = os.path.join(subtitle_path, os.path.basename(src_path))
        shutil.move(src_path, ttml_path)
        srt_path = ttml_path.replace("ttml", "srt")
        convert_subtitle_ttml_to_srt(ttml_path, srt_path, False)
        os.remove(ttml_path)
        return srt_path

    def info(self, url: str, index: int, proxy: str = None) -> str or None:
        ydl_opts = {
            'skip_download': True,
            'quiet': True,
            'no_warnings': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        result = {}

        # YouTube 自动生成字幕
        auto_captions = info.get('automatic_captions', {}) or {}
        all_subs = {'auto': auto_captions}

        for kind, sub_dict in all_subs.items():
            for lang, entries in sub_dict.items():
                key = f"{lang}"
                result[key] = [
                    {'ext': e['ext'], 'url': e['url']}
                    for e in entries
                ]
        logger.info(json.dumps(result))
        return None


if __name__ == "__main__":
    init_config()
    subscriber = SubTitleTranscriber()
    url = "https://www.youtube.com/watch?v=gSNFJbgoaHI"
    # subscriber.info(url, 1)
    path = subscriber.subtitle(url, 13, "http://localhost:7890")
    logger.info(path)
