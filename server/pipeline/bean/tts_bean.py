from dataclasses import dataclass

from utils import const
from utils.const import TTS_LIST_AZURE_TTS_V1_VAL


@dataclass
class TTSBean:
    tts_server: str = TTS_LIST_AZURE_TTS_V1_VAL
    tts_voice: str = ""
    tts_volume: float = 0
    tts_speed: float = 0
    tts_full_path: str = ""
    final_subtitle_path: str = ""
    tts_dubbing_strategy: int = const.DUBBING_STRATEGY_TIMELINE_FIRST

    def __str__(self) -> str:
        return f"""
        TTSBean(
            tts_server: {self.tts_server}, 
            tts_voice: {self.tts_voice}, 
            tts_volume: {self.tts_volume}, 
            tts_speed: {self.tts_speed}, 
            tts_full_path: {self.tts_full_path},
            tts_dubbing_strategy: {self.tts_dubbing_strategy}
        )
        """
