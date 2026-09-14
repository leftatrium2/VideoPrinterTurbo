import asyncio
import os
from typing import Optional

import config.config as _config
from pipeline.tts.azure_tts_v1 import AzureTTSV1
from pipeline.tts.azure_tts_v2 import AzureTTSV2
from pipeline.tts.base import TTSBase
from pipeline.tts.google_gemini_tts import GoogleGeminiTTS
from pipeline.tts.siliconflow_tts import SiliconFlowTTS
from pipeline.utils.pipeline_video_downloader_utils import init_downloader
from utils import const
from utils.exception import VPTException
from utils.file_utils import get_llm_rewrite_path


def tts_from_subtitle(
        tts_engine: str,
        subtitle_path: str,
        voice: str,
        lang: str,
        api_key: Optional[str] = None,
        region: Optional[str] = None,
        proxy_type: int = const.PROXY_CONFIG_TYPE_UNKNOWN,
        proxy_url: Optional[str] = None

) -> bool:
    tts_service: Optional[TTSBase] = None
    if tts_engine == const.TTS_LIST_AZURE_TTS_V1_VAL:
        tts_service = AzureTTSV1(proxy_type=proxy_type, proxy_url=proxy_url)
    elif tts_engine == const.TTS_LIST_AZURE_TTS_V2_VAL:
        if not api_key:
            raise VPTException(const.PIPELINE_ERR_VALUE, "api key is empty!")
        if not region:
            raise VPTException(const.PIPELINE_ERR_VALUE, "region is empty!")
        tts_service = AzureTTSV2(
            api_key=api_key,
            region=region,
            proxy_type=proxy_type,
            proxy_url=proxy_url
        )
    elif tts_engine == const.TTS_LIST_SILICON_FLOW_TTS_VAL:
        if not api_key:
            raise VPTException(const.PIPELINE_ERR_VALUE, "api key is empty!")
        tts_service = SiliconFlowTTS(
            api_key=api_key,
            proxy_type=proxy_type,
            proxy_url=proxy_url
        )
    elif tts_engine == const.TTS_LIST_GOOGLE_GEMINI_TTS_VAL:
        if not api_key:
            raise VPTException(const.PIPELINE_ERR_VALUE, "api key is empty!")
        tts_service = GoogleGeminiTTS(
            api_key=api_key,
            proxy_type=proxy_type,
            proxy_url=proxy_url
        )
    if not tts_service:
        return False
    tts_service.rewrite(subtitle_path, lang, voice)
    return True


if __name__ == "__main__":
    _config.init_config()
    init_downloader()

    lang = asyncio.run(get_llm_rewrite_path())
    llm_rewrite_path = os.path.join(lang, "20260720215545133997.srt")

    tts_from_subtitle(
        tts_engine="TTS_LIST_AZURE_TTS_V2",
        subtitle_path=llm_rewrite_path,
        voice="zh-CN-XiaoxiaoNeural",
        lang="zh-CN",
        api_key="",
        region="koreacentral",
        proxy_type=const.PROXY_CONFIG_TYPE_HTTPS,
        proxy_url="http://127.0.0.1:7890"
    )
