from utils import const


class TTSUtils:
    @staticmethod
    def get_name(engine: int) -> str or None:
        if engine == const.TTS_LIST_AZURE_TTS_V1:
            return "AZURE TTS V1"
        elif engine == const.TTS_LIST_AZURE_TTS_V2:
            return "AZURE TTS V2"
        elif engine == const.TTS_LIST_SILICON_FLOW_TTS:
            return "SILICON FLOW TTS"
        elif engine == const.TTS_LIST_GOOGLE_GEMINI_TTS:
            return "GOOGLE GEMINI TTS"
        elif engine == const.TTS_LIST_XIAOMI_MIMO_TTS:
            return "XIAOMI MIMO TTS"
        return None
