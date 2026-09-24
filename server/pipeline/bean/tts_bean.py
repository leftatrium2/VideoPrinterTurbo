from dataclasses import dataclass

from utils.const import TTS_LIST_AZURE_TTS_V1_VAL


@dataclass
class TTSBean:
    tts_server: str = TTS_LIST_AZURE_TTS_V1_VAL
    tts_voice: str = ""
    tts_volume: float = 0
    tts_speed: float = 0
    tts_full_path: str = ""

    def __str__(self) -> str:
        return f"""
        TTSBean(
            tts_server: {self.tts_server}, 
            tts_voice: {self.tts_voice}, 
            tts_volume: {self.tts_volume}, 
            tts_speed: {self.tts_speed}, 
            tts_full_path: {self.tts_full_path}
        )
        """
