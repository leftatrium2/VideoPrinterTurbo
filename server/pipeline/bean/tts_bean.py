from dataclasses import dataclass

from utils.const import TTS_LIST_AZURE_TTS_V1_VAL


@dataclass
class TTSBean:
    tts_server: str = TTS_LIST_AZURE_TTS_V1_VAL
    tts_voice: str = ""
    tts_volume: str = ""
    tts_speed: float = 0
    tts_path: str = ""
