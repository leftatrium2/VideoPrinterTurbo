import asyncio
import logging
import os
import tempfile
from urllib.parse import urlparse

from config.config import init_config
from pipeline.tts.base import TTSBase
from utils.file_utils import get_tts_rewrite_path, get_llm_rewrite_path
from utils.tts_utils import TTSUtils


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

    __api_key = None
    __region = None
    __proxy = None
    __bitrate = "128k"

    def config(self, api_key: str = None, region: str = None, proxy: str = None):
        self.__api_key = api_key
        self.__region = region
        self.__proxy = proxy

    def rewrite(self, subtitle_path: str, lang: str, voice: str) -> str or None:
        if not os.path.exists(subtitle_path):
            logging.error(f"File {subtitle_path} does not exist")
            return None
        name, ext = os.path.splitext(os.path.basename(subtitle_path))
        path = asyncio.run(get_tts_rewrite_path())
        subs = TTSUtils.parse_srt(subtitle_path)
        if not subs:
            logging.error(f"No subtitle in {subtitle_path}")
            return None
        tts_file_path = os.path.join(path, f"{name}.m4a")
        synth_kwargs = {
            "voice": voice, "key": self.__api_key,
            "proxy": self.__proxy,
            "region": self.__region, "lang": lang,
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            timeline = TTSUtils.build_timeline(subs, AzureTTSV2.synthesize, synth_kwargs, tmp_dir)
            TTSUtils.export_timeline(timeline, tts_file_path, bitrate=self.__bitrate)


if __name__ == "__main__":
    tts: TTSBase = AzureTTSV2()
    init_config()
    lang = asyncio.run(get_llm_rewrite_path())
    llm_rewrite_path = os.path.join(lang, "gSNFJbgoaHI.cn.srt")
    tts.config(
        api_key="",
        region="koreacentral",
    )
    tts.rewrite(llm_rewrite_path, "zh-CN", "zh-CN-XiaoxiaoNeural")
