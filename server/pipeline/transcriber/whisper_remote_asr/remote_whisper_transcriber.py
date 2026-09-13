import asyncio
import logging
from typing import Optional

import config.config as _config
from pipeline.transcriber.base import BaseTranscriber
from pipeline.transcriber.whisper_remote_asr.engine.vllm_whisper_transcriber import VLLMWhisperTranscriber
from pipeline.transcriber.whisper_remote_asr.engine.whisper_cpp_transcriber import WhisperCppTranscriber
from pipeline.utils.pipeline_video_downloader_utils import init_downloader
from utils import const
from utils.exception import VPTException
from utils.file_utils import get_video_to_text_path

logger = logging.getLogger(__name__)


class RemoteWhisperTranscriber(BaseTranscriber):
    def __init__(
            self,
            remote_whisper_type=const.TASK_CONFIG_REMOTE_VLLM_WHISPER,
            remote_server_url: Optional[str] = None,
            remote_server_model: Optional[str] = None,
            language: Optional[str] = None
    ):
        self.__remote_whisper_type = remote_whisper_type
        self.__remote_server_url = remote_server_url
        self.__remote_server_model = remote_server_model
        self.__language = language
        self.__proxy = None

    def config(self, proxy: Optional[str] = None):
        if proxy:
            self.__proxy = proxy

    def transcribe(self, audio_path: str) -> Optional[str]:
        if not self.__remote_server_url:
            raise VPTException(const.PIPELINE_ERR_VALUE, "remote_server_url is empty!")
        output_path = asyncio.run(get_video_to_text_path())
        srt_path = None
        if self.__remote_whisper_type == const.TASK_CONFIG_REMOTE_VLLM_WHISPER:
            if not self.__remote_server_model:
                raise VPTException(const.PIPELINE_ERR_VALUE, "remote_server_model is empty!")
            vllm_whisper_transcriber = VLLMWhisperTranscriber(self.__remote_server_url, self.__remote_server_model,
                                                              self.__language)
            srt_path = vllm_whisper_transcriber.transcribe_mp3_to_srt(audio_path, output_path)
        elif self.__remote_whisper_type == const.TASK_CONFIG_REMOTE_WHISPER_CPP:
            whisper_cpp_transcriber = WhisperCppTranscriber(self.__remote_server_url, self.__language)
            srt_path = whisper_cpp_transcriber.transcribe_mp3_to_srt(audio_path, output_path)
        return srt_path


if __name__ == "__main__":
    _config.init_config()
    init_downloader()
    remote_whisper_transcriber = RemoteWhisperTranscriber(
        remote_whisper_type=const.TASK_CONFIG_REMOTE_WHISPER_CPP,
        remote_server_url="http://192.168.0.105:8004/inference",
        remote_server_model="",
        language="zh"
    )
    result = remote_whisper_transcriber.transcribe("/Users/sunxiao5/1-asr.mp3")
    if result:
        print(result)
    else:
        print("transcribe failed")
