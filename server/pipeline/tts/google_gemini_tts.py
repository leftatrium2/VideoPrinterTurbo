import asyncio
import logging
import os
import tempfile
import wave
from typing import Optional

from config.config import init_config
from pipeline.tts.base import TTSBase
from utils import const
from utils.file_utils import get_tts_rewrite_path, get_llm_rewrite_path
from utils.tts_utils import TTSUtils


class GoogleGeminiTTS(TTSBase):

    @staticmethod
    def synthesize(
            text,
            voice,
            out_path,
            api_key=None,
            model="gemini-2.5-flash-preview-tts",
            proxy=None,
            **_,
    ):
        """
        voice: Gemini 内置音色名，如 Kore、Puck、Zephyr、Charon 等（共 30 个，
               完整列表见官方文档）。
        model: TTS 模型名，如 gemini-2.5-flash-preview-tts /
               gemini-2.5-pro-preview-tts，官方也在推出更新的型号，
               如有需要可通过 --model 覆盖。
        """
        from google import genai
        from google.genai import types
        http_options = types.HttpOptions(client_args={"proxy": proxy}) if proxy else None

        client = genai.Client(api_key=api_key, http_options=http_options) if api_key else genai.Client(
            http_options=http_options)

        chat = client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice
                        )
                    )
                ),
            ),
        )
        response = chat.send_message(text)

        part = response.candidates[0].content.parts[0]
        pcm_data = part.inline_data.data

        # Gemini TTS 固定输出 16-bit / 24000Hz / 单声道 PCM
        with wave.open(out_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(pcm_data)

    def __init__(self,
                 api_key: str,
                 proxy_type: int = const.PROXY_CONFIG_TYPE_UNKNOWN,
                 proxy_url: Optional[str] = None):
        self.__api_key = api_key
        self.__bitrate = "128k"
        self.__proxy_type = proxy_type
        self.__proxy_url = proxy_url

    def rewrite(self, subtitle_path: str, lang: str, voice: str) -> Optional[str]:
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
            "voice": voice, "api_key": self.__api_key,
            "model": "gemini-2.5-flash-preview-tts",
        }
        if self.__proxy_url:
            synth_kwargs["proxy"] = self.__proxy_url
        with tempfile.TemporaryDirectory() as tmp_dir:
            timeline = TTSUtils.build_timeline(subs, GoogleGeminiTTS.synthesize, synth_kwargs, tmp_dir)
            TTSUtils.export_timeline(timeline, tts_file_path, bitrate=self.__bitrate)

        return tts_file_path


if __name__ == "__main__":
    init_config()
    lang = asyncio.run(get_llm_rewrite_path())
    llm_rewrite_path = os.path.join(lang, "20260720215545133997.srt")
    tts: TTSBase = GoogleGeminiTTS(
        api_key="",
        proxy_type=const.PROXY_CONFIG_TYPE_HTTPS,
        proxy_url="http://127.0.0.1:7890"
    )
    tts.rewrite(llm_rewrite_path, "zh-CN", "Kore")
