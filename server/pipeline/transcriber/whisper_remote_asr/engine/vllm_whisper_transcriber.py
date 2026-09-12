import logging
import os.path
from pathlib import Path
from typing import Optional

import requests

from pipeline.transcriber.whisper_remote_asr.engine.remote_whisper_common import convert_audio_parts, write_srt
from pipeline.utils.pipeline_video_downloader_utils import init_downloader
import config.config as _config

logger = logging.getLogger(__name__)


class VLLMWhisperTranscriber(object):
    def __init__(
            self,
            vllm_url,
            model,
            language
    ):
        self.__vllm_url = vllm_url
        self.__model = model
        self.__language = language

    def transcribe_mp3_to_srt(self,
                              mp3_path: str,
                              output_dir_path: str
                              ) -> Optional[str]:
        audio_path = Path(mp3_path).expanduser().resolve()
        if not audio_path.is_file():
            raise FileNotFoundError(f"找不到 MP3 文件：{mp3_path}")
        srt_path = Path(output_dir_path).expanduser().resolve()
        if not srt_path.is_dir():
            srt_path.mkdir(parents=True, exist_ok=True)
        srt_path = Path(os.path.join(output_dir_path, f"{audio_path.stem}.srt"))

        all_segments = []
        with convert_audio_parts(audio_path) as parts:
            for number, part in enumerate(parts, start=1):
                logger.info(f"vLLM 正在转写第 {number}/{len(parts)} 段：{part.path.name}")
                with part.path.open("rb") as audio_file:
                    response = requests.post(
                        self.__vllm_url,
                        files={"file": (part.path.name, audio_file, "audio/mpeg")},
                        data={
                            "model": self.__model,
                            "language": self.__language,
                            "response_format": "verbose_json",
                            "temperature": "0",
                        },
                        timeout=(10, 3600),
                    )
                    response.raise_for_status()
                    result = response.json()

                    for segment in result.get("segments") or []:
                        all_segments.append((
                            float(segment["start"]) + part.offset_seconds,
                            float(segment["end"]) + part.offset_seconds,
                            segment["text"],
                        ))

        write_srt(srt_path, all_segments)
        logger.info(f"已生成：{srt_path}")
        return str(srt_path)


if __name__ == "__main__":
    _config.init_config()
    init_downloader()
    whisper_transcriber = VLLMWhisperTranscriber(
        vllm_url="http://192.168.0.105:8003/v1/audio/transcriptions",
        model="whisper-large-v3-turbo",
        language="zh"
    )
    whisper_transcriber.transcribe_mp3_to_srt(
        mp3_path="/Users/sunxiao5/1-asr.mp3",
        output_dir_path="/Users/sunxiao5"
    )
