import config.config as _config
from pipeline.tts.azure_tts_v1 import AzureTTSV1
from pipeline.tts.azure_tts_v2 import AzureTTSV2
from pipeline.tts.base import TTSBase
from pipeline.tts.google_gemini_tts import GoogleGeminiTTS
from pipeline.tts.siliconflow_tts import SiliconFlowTTS
from pipeline.utils.pipeline_video_downloader_utils import init_downloader
from utils import const


def tts(tts_engine: str, subtitle_path: str, lang: str, voice: str, api_key: str = None,
        region: str = None, proxy: str = None) -> bool:
    tts: TTSBase = None
    if tts_engine == const.TTS_LIST_AZURE_TTS_V1_VAL:
        tts = AzureTTSV1()
    elif tts_engine == const.TTS_LIST_AZURE_TTS_V2_VAL:
        tts = AzureTTSV2()
    elif tts_engine == const.TTS_LIST_SILICON_FLOW_TTS_VAL:
        tts = SiliconFlowTTS()
    elif tts_engine == const.TTS_LIST_GOOGLE_GEMINI_TTS_VAL:
        tts = GoogleGeminiTTS()
    if not tts:
        return False
    tts.config(api_key=api_key, region=region, proxy=proxy)
    tts.rewrite(subtitle_path, lang, voice)
    return True


if __name__ == "__main__":
    _config.init_config()
    init_downloader()
