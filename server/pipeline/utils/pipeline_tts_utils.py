from pipeline.tts.azure_tts_v1 import AzureTTSV1
from pipeline.tts.base import TTSBase
from pipeline.tts.google_gemini_tts import GoogleGeminiTTS

import config.config as _config
from pipeline.utils.pipeline_video_downloader_utils import init_downloader


def tts(tts_engine: str, subtitle_path: str, lang: str, voice: str, api_key: str = None,
        region: str = None, proxy: str = None) -> bool:
    tts: TTSBase = None
    if tts_engine == "Azure TTS V1":
        tts = AzureTTSV1()
    elif tts_engine == "Google Gemini TTS":
        tts = GoogleGeminiTTS()
    if not tts:
        return False
    tts.config(api_key=api_key, region=region, proxy=proxy)
    tts.rewrite(subtitle_path, lang, voice)
    return True


if __name__ == "__main__":
    _config.init_config()
    init_downloader()
