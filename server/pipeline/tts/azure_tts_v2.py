import asyncio
import os
import tempfile
from typing import Optional
from urllib.parse import urlparse

from pipeline.tts.base import TTSBase
from pipeline.utils.pipeline_video_downloader_utils import init_downloader
from utils import const
from utils.exception import VPTException
from utils.file_utils import get_tts_rewrite_path, get_llm_rewrite_path
from utils.tts_utils import TTSUtils
import config.config as _config


class AzureTTSV2(TTSBase):
    @staticmethod
    def _apply_proxy(speech_config, proxy: str):
        """
        Azure Speech SDK 的代理接口是 set_proxy(hostname, port, username, password)，
        不接受一整个 URL，这里把 http://user:pass@host:port 形式的 proxy 解析开。
        """
        parsed = urlparse(proxy)
        if not parsed.hostname or not parsed.port:
            raise ValueError(f"无法解析 proxy 地址: {proxy!r}，需要形如 http://host:port")
        speech_config.set_proxy(
            parsed.hostname, parsed.port, parsed.username, parsed.password
        )

    @staticmethod
    def _escape_ssml(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

    # 调用官方 Azure Speech SDK 合成语音（同步阻塞调用）
    @staticmethod
    def synthesize(text, voice, out_path, key=None, region=None, lang="zh-CN", proxy=None, **_):
        import azure.cognitiveservices.speech as speechsdk

        if not key or not region:
            raise ValueError("provider=azure 需要提供 --key 和 --region")

        speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
        )
        if proxy:
            AzureTTSV2._apply_proxy(speech_config, proxy)
        audio_config = speechsdk.audio.AudioOutputConfig(filename=out_path)
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=audio_config
        )

        ssml = (
            f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
            f'xml:lang="{lang}">'
            f'<voice name="{voice}">{AzureTTSV2._escape_ssml(text)}</voice>'
            f"</speak>"
        )
        result = synthesizer.speak_ssml_async(ssml).get()

        if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
            details = result.cancellation_details
            raise RuntimeError(
                f"azure tts v2 合成失败: {result.reason}, "
                f"{details.reason if details else ''} "
                f"{details.error_details if details else ''}"
            )

    def __init__(
            self,
            api_key: str,
            region: str,
            proxy_type: int = const.PROXY_CONFIG_TYPE_UNKNOWN,
            proxy_url: Optional[str] = None
    ):
        self.__api_key = api_key
        self.__region = region
        self.__bitrate = "128k"
        self.__proxy_type = proxy_type
        self.__proxy_url = proxy_url

    def rewrite(self, subtitle_path: str, lang: str, voice: str) -> Optional[str]:
        if not os.path.exists(subtitle_path):
            raise VPTException(const.PIPELINE_ERR_FILE_NOT_FOUND, f"File {subtitle_path} does not exist")
        name, ext = os.path.splitext(os.path.basename(subtitle_path))
        path = asyncio.run(get_tts_rewrite_path())
        subs = TTSUtils.parse_srt(subtitle_path)
        if not subs:
            raise VPTException(const.PIPELINE_ERR_TTS_SRT_PARSE, f"No subtitle in {subtitle_path}")
        tts_file_path = os.path.join(path, f"{name}.m4a")
        synth_kwargs = {
            "voice": voice, "key": self.__api_key,
            "proxy": self.__proxy_url,
            "region": self.__region,
            "lang": lang,
        }
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                timeline = TTSUtils.build_timeline(subs, AzureTTSV2.synthesize, synth_kwargs, tmp_dir)
                TTSUtils.export_timeline(timeline, tts_file_path, bitrate=self.__bitrate)
                return tts_file_path
        except Exception as ex:
            raise VPTException(const.PIPELINE_ERR_TTS_CONVERT, str(ex), ex) from ex


if __name__ == "__main__":
    _config.init_config()
    init_downloader()

    azure_tts_v2 = AzureTTSV2(
        api_key="",
        region="koreacentral",
        proxy_type=const.PROXY_CONFIG_TYPE_HTTPS,
        proxy_url="http://127.0.0.1:7890"
    )
    lang = asyncio.run(get_llm_rewrite_path())
    llm_rewrite_path = os.path.join(lang, "20260720215545133997.srt")
    azure_tts_v2.rewrite(llm_rewrite_path, lang="zh-CN", voice="zh-CN-XiaoxiaoNeural")
