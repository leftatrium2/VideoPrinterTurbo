import logging
import os
import re
from pathlib import Path
from typing import Optional

import requests

from pipeline.transcriber.whisper_remote_asr.engine.remote_whisper_common import convert_audio_parts, write_srt
from pipeline.utils.pipeline_video_downloader_utils import init_downloader
import config.config as _config

logger = logging.getLogger(__name__)

TIME_LINE = re.compile(
    r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*"
    r"(\d{2}:\d{2}:\d{2}[,.]\d{3})"
)


def timestamp_to_seconds(value: str) -> float:
    hours, minutes, remaining = value.replace(",", ".").split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(remaining)


def parse_srt(srt_text: str, offset_seconds: float):
    segments = []

    for block in re.split(r"\r?\n\s*\r?\n", srt_text.strip()):
        lines = block.splitlines()

        for line_index, line in enumerate(lines):
            match = TIME_LINE.fullmatch(line.strip())
            if not match:
                continue

            text = "\n".join(lines[line_index + 1:]).strip()
            if text:
                segments.append((
                    timestamp_to_seconds(match.group(1)) + offset_seconds,
                    timestamp_to_seconds(match.group(2)) + offset_seconds,
                    text,
                ))
            break

    return segments


class WhisperCppTranscriber(object):
    def __init__(
            self,
            whisper_cpp_url: str,
            language: Optional[str] = None
    ):
        self.__whisper_cpp_url = whisper_cpp_url
        self.__language = language

    def transcribe_mp3_to_srt(self,
                              mp3_path: str,
                              output_dir_path: str
                              ) -> Optional[str]:
        if not mp3_path:
            raise FileNotFoundError("mp3_path is empty")
        audio_path = Path(mp3_path).expanduser().resolve()
        if not audio_path.is_file():
            raise FileNotFoundError(f"{mp3_path} is not a file")
        srt_path = Path(output_dir_path).expanduser().resolve()
        if not srt_path.is_dir():
            srt_path.mkdir(parents=True, exist_ok=True)
        srt_path = Path(os.path.join(output_dir_path, f"{audio_path.stem}.srt"))

        all_segments = []
        with convert_audio_parts(audio_path) as parts:
            for number, part in enumerate(parts, start=1):
                logger.info(f"whisper.cpp 正在转写第 {number}/{len(parts)} 段：{part.path.name}")
                with part.path.open("rb") as audio_file:
                    params_data = {
                        "temperature": "0.0",
                        "response_format": "srt",
                    }
                    if self.__language:
                        params_data['language'] = self.__language
                    response = requests.post(
                        self.__whisper_cpp_url,
                        files={"file": (part.path.name, audio_file, "audio/mpeg")},
                        data=params_data,
                        timeout=(10, 3600),
                    )
                    response.raise_for_status()
                    all_segments.extend(parse_srt(response.text, part.offset_seconds))

        write_srt(srt_path, all_segments)
        logger.info(f"已生成：{srt_path}")
        return str(srt_path)


if __name__ == "__main__":
    _config.init_config()
    init_downloader()
    whisper_transcriber = WhisperCppTranscriber(
        "http://192.168.0.105:8004/inference"
    )
    whisper_transcriber.transcribe_mp3_to_srt("/Users/sunxiao5/1-asr.mp3", "/Users/sunxiao5")
