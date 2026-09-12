from typing import Optional

from pipeline.transcriber.base import BaseTranscriber
from pipeline.transcriber.whisper_remote_asr.engine.vllm_whisper_transcriber import VLLMWhisperTranscriber
from utils import const


class RemoteWhisperTranscriber(BaseTranscriber):
    def __init__(
            self,
            remote_whisper_type=1,
            remote_server_url: str = "",
            remote_server_model: str = ""
    ):
        self.__remote_whisper_type = remote_whisper_type
        self.__remote_server_url = remote_server_url
        self.__remote_server_model = remote_server_model
        self.__proxy = None

    def config(self, proxy: Optional[str] = None, **args):
        if proxy:
            self.__proxy = proxy

    def transcribe(self, audio_path: str) -> Optional[str]:
        remote_whisper_transcriber = None
        if self.__remote_whisper_type == const.TASK_CONFIG_REMOTE_VLLM_WHISPER:
            remote_whisper_transcriber = VLLMWhisperTranscriber(self.__remote_server_url, self.__remote_server_model)
            pass
        elif self.__remote_whisper_type == const.TASK_CONFIG_REMOTE_WHISPER_CPP:
            pass
